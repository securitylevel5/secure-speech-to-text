#!/usr/bin/env python3
"""
Secure Speech-to-Text - Interactive transcription wrapper

End-to-end workflow: Transcribe, Generate Executive Summary, Secure Delete
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on system env vars

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from best_effort_delete import best_effort_delete_ssd

# Default directories
DEFAULT_OUTPUT_DIR = Path("output")


def prompt_yes_no(question: str, default: bool = True, interactive: bool = True) -> bool:
    """Prompt user for yes/no confirmation. Returns default if non-interactive."""
    if not interactive:
        return default
    
    if default:
        prompt_str = f"{question} [Y/n]: "
    else:
        prompt_str = f"{question} [y/N]: "
    
    response = input(prompt_str).strip().lower()
    
    if not response:
        return default
    return response in ('y', 'yes')


def create_output_folder(audio_path: Path, base_output_dir: Path) -> Path:
    """Create timestamped output folder for results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{audio_path.stem}_{timestamp}"
    output_dir = base_output_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_transcription(audio_path: Path, output_dir: Path, diarize: bool = True) -> bool:
    """Run WhisperX transcription on the audio file."""
    print(f"\n{'='*60}")
    print("TRANSCRIPTION")
    print(f"{'='*60}")
    print(f"Input:  {audio_path}")
    print(f"Output: {output_dir}")
    print()
    
    cmd = [
        "whisperx",
        str(audio_path),
        "--output_dir", str(output_dir),
        "--output_format", "all",
    ]

    # Allow forcing WhisperX device/compute type via env vars (useful for CPU containers)
    wx_device = os.getenv("WHISPERX_DEVICE")
    wx_compute_type = os.getenv("WHISPERX_COMPUTE_TYPE")
    if wx_device:
        cmd += ["--device", wx_device]
    if wx_compute_type:
        cmd += ["--compute_type", wx_compute_type]
    
    if diarize:
        cmd.append("--diarize")
    
    # Propagate Hugging Face token to all expected env vars for WhisperX/pyannote
    env = os.environ.copy()
    hf_token = env.get("HUGGINGFACE_HUB_TOKEN")
    if hf_token:
        env.setdefault("HF_TOKEN", hf_token)
        env.setdefault("HUGGINGFACE_TOKEN", hf_token)

    try:
        result = subprocess.run(cmd, check=True, env=env)
        print("\n✓ Transcription complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Transcription failed: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ Error: whisperx not found. Is it installed?")
        return False


def get_transcript_content(output_dir: Path) -> str | None:
    """Read the transcript text file from output directory."""
    txt_files = list(output_dir.glob("*.txt"))
    if not txt_files:
        return None
    
    # Use the first .txt file found
    transcript_file = txt_files[0]
    return transcript_file.read_text(encoding="utf-8")


def generate_executive_summary(transcript: str, output_dir: Path) -> bool:
    """Generate executive summary using OpenAI-compatible API."""
    print(f"\n{'='*60}")
    print("EXECUTIVE SUMMARY GENERATION")
    print(f"{'='*60}")
    
    if OpenAI is None:
        print("✗ Error: openai package not installed. Run: pip install openai")
        return False
    
    api_base = os.getenv("API_BASE_URL", "http://localhost:1234/v1")
    api_key = os.getenv("API_KEY", "lm-studio")
    model_name = os.getenv("MODEL_NAME", "local-model")
    
    print(f"API:   {api_base}")
    print(f"Model: {model_name}")
    print()
    
    client = OpenAI(base_url=api_base, api_key=api_key)
    
    system_prompt = """You are an assistant that creates executive summaries of meeting transcripts.
Create a concise executive summary of the following transcript, highlighting:
- Key discussion points
- Decisions made
- Action items
- Participants (if identifiable from speaker labels)

Format the summary in clear sections with headers."""

    try:
        print("Generating summary...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please summarize this transcript:\n\n{transcript}"}
            ],
            temperature=0.3,
        )
        
        summary = response.choices[0].message.content
        
        # Save summary to file
        summary_file = output_dir / "executive_summary.md"
        summary_file.write_text(f"# Executive Summary\n\n{summary}", encoding="utf-8")
        
        print(f"\n✓ Summary saved to: {summary_file}")
        print(f"\n{'─'*60}")
        print(summary)
        print(f"{'─'*60}")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to generate summary: {e}")
        return False


def secure_delete_audio(audio_path: Path) -> bool:
    """Securely delete the source audio file."""
    print(f"\n{'='*60}")
    print("SECURE DELETION")
    print(f"{'='*60}")
    print(f"File: {audio_path}")
    print()
    
    try:
        best_effort_delete_ssd(str(audio_path))
        print("✓ Source audio deleted (best-effort)")
        return True
    except Exception as e:
        print(f"✗ Failed to delete: {e}")
        return False


def print_summary(output_dir: Path, audio_path: Path, transcribed: bool, summarized: bool, deleted: bool):
    """Print final summary of actions taken."""
    print(f"\n{'='*60}")
    print("COMPLETE")
    print(f"{'='*60}")
    print(f"Output folder: {output_dir.absolute()}")
    print()
    print("Actions performed:")
    print(f"  {'✓' if transcribed else '✗'} Transcription")
    print(f"  {'✓' if summarized else '✗'} Executive Summary")
    print(f"  {'✓' if deleted else '✗'} Secure Deletion")
    print()
    
    if output_dir.exists():
        print("Output files:")
        for f in sorted(output_dir.iterdir()):
            size = f.stat().st_size
            print(f"  - {f.name} ({size:,} bytes)")
    
    # Show delete command if source audio was not deleted
    if not deleted and audio_path.exists():
        print(f"\nTo securely delete source audio:")
        print(f"  python best_effort_delete.py {audio_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Secure Speech-to-Text - Transcription workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts at each step)
  python secure_speech_to_text.py input/meeting.m4a

  # Non-interactive mode (runs full pipeline)
  python secure_speech_to_text.py input/meeting.m4a -y

  # Skip summary generation
  python secure_speech_to_text.py input/meeting.m4a -y --no-summary

  # Custom output directory
  python secure_speech_to_text.py meeting.m4a --output-dir ./my-transcripts

Environment variables (or .env file):
  API_BASE_URL  - OpenAI-compatible API endpoint (default: http://localhost:1234/v1)
  API_KEY       - API key (default: lm-studio)
  MODEL_NAME    - Model to use for summaries (default: local-model)
        """
    )
    
    parser.add_argument("audio_file", help="Path to audio file to transcribe")
    parser.add_argument(
        "-y", "--no-interactive",
        action="store_true",
        help="Non-interactive mode: skip prompts, run full pipeline"
    )
    parser.add_argument(
        "--no-diarize",
        action="store_true",
        help="Disable speaker diarization"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip executive summary generation"
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Skip secure deletion of source audio"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Base output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    
    audio_path = Path(args.audio_file)
    interactive = not args.no_interactive
    
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("SECURE SPEECH-TO-TEXT")
    print(f"{'='*60}")
    print(f"Audio file: {audio_path.name}")
    print(f"Size: {audio_path.stat().st_size:,} bytes")
    if not interactive:
        print("Mode: Non-interactive")
    print()
    
    # Create output folder
    output_dir = create_output_folder(audio_path, args.output_dir)
    
    # Track what was done
    transcribed = False
    summarized = False
    deleted = False
    
    # Step 1: Transcription
    if prompt_yes_no("Transcribe audio?", default=True, interactive=interactive):
        transcribed = run_transcription(
            audio_path, 
            output_dir, 
            diarize=not args.no_diarize
        )
    else:
        print("Skipping transcription.")
    
    # Step 2: Executive Summary (only if transcription succeeded or exists)
    if not args.no_summary:
        transcript = get_transcript_content(output_dir)
        if transcript:
            if prompt_yes_no("Generate executive summary?", default=True, interactive=interactive):
                summarized = generate_executive_summary(transcript, output_dir)
            else:
                print("Skipping summary generation.")
        elif transcribed:
            print("No transcript file found, skipping summary.")
    else:
        print("Skipping summary generation (--no-summary).")
    
    # Step 3: Secure Deletion
    if not args.no_delete:
        if audio_path.exists():
            # Default to False for deletion (safer)
            if prompt_yes_no("Securely delete source audio?", default=False, interactive=interactive):
                deleted = secure_delete_audio(audio_path)
            else:
                print("Source audio preserved.")
    else:
        print("Skipping secure deletion (--no-delete).")
    
    # Final summary
    print_summary(output_dir, audio_path, transcribed, summarized, deleted)


if __name__ == "__main__":
    main()
