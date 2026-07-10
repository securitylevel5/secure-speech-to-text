#!/usr/bin/env python3
"""
Token Counter - Calculate tokens in a file for LM Studio context sizing

This utility helps you determine the token count of transcript files,
useful for sizing context windows in LM Studio or other LLM interfaces.
"""

import sys
import argparse
from pathlib import Path


def count_tokens_tiktoken(text, model="gpt-4"):
    """Count tokens using tiktoken (works for most models as approximation)"""
    try:
        import tiktoken
    except ImportError:
        print("Error: tiktoken not installed. Run: pip install tiktoken")
        sys.exit(1)
    
    # Get the encoding for the model
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base (GPT-4, GPT-3.5-turbo)
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(text)
    return len(tokens)


def count_tokens_transformers(text, model_name="gpt2"):
    """Count tokens using transformers library (more accurate for specific models)"""
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("Error: transformers not installed. Run: pip install transformers")
        sys.exit(1)
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(text)
    return len(tokens)


def read_file(filepath):
    """Read file content"""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File '{filepath}' not found")
        sys.exit(1)
    
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Try with different encoding
        return path.read_text(encoding='latin-1')


def format_size(size_bytes):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0


def main():
    parser = argparse.ArgumentParser(
        description='Count tokens in a file for LM Studio context sizing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m utils.token_counter document.txt
  python -m utils.token_counter document.txt --method transformers --model mistralai/Mistral-7B-v0.1
  python -m utils.token_counter document.txt --method tiktoken --model gpt-4
        """
    )
    
    parser.add_argument('file', help='File to count tokens in')
    parser.add_argument(
        '--method',
        choices=['tiktoken', 'transformers'],
        default='tiktoken',
        help='Tokenizer method (default: tiktoken - faster, good approximation)'
    )
    parser.add_argument(
        '--model',
        default=None,
        help='Model name for tokenizer (default: gpt-4 for tiktoken, gpt2 for transformers)'
    )
    
    args = parser.parse_args()
    
    # Set default model based on method if not specified
    if args.model is None:
        if args.method == 'tiktoken':
            args.model = 'gpt-4'
        else:
            args.model = 'gpt2'
    
    # Read file
    print(f"Reading file: {args.file}")
    content = read_file(args.file)
    
    # Get file stats
    file_path = Path(args.file)
    file_size = file_path.stat().st_size
    char_count = len(content)
    word_count = len(content.split())
    line_count = content.count('\n') + 1
    
    # Count tokens
    print(f"Counting tokens using {args.method}...")
    
    if args.method == 'tiktoken':
        token_count = count_tokens_tiktoken(content, args.model)
    else:
        token_count = count_tokens_transformers(content, args.model)
    
    # Display results
    print("\n" + "="*60)
    print("TOKEN COUNT RESULTS")
    print("="*60)
    print(f"File:              {args.file}")
    print(f"File size:         {format_size(file_size)}")
    print(f"Characters:        {char_count:,}")
    print(f"Words:             {word_count:,}")
    print(f"Lines:             {line_count:,}")
    print(f"\nTokens:            {token_count:,}")
    print(f"Tokenizer:         {args.method} ({args.model})")
    print("="*60)
    
    # Context window recommendations
    print("\nLM STUDIO CONTEXT RECOMMENDATIONS:")
    print("-" * 60)
    
    recommended_contexts = [4096, 8192, 16384, 32768, 65536, 131072]
    for ctx in recommended_contexts:
        if token_count <= ctx * 0.9:  # Leave 10% buffer
            print(f"✓ Minimum recommended: {ctx:,} tokens")
            if ctx < max(recommended_contexts):
                next_ctx = recommended_contexts[recommended_contexts.index(ctx) + 1]
                print(f"  Suggested (with buffer): {next_ctx:,} tokens")
            break
    else:
        print(f"⚠ File requires context > {max(recommended_contexts):,} tokens")
    
    print(f"\nToken to context ratio: {(token_count / 4096):.2f}x (4K base)")


if __name__ == "__main__":
    main()

