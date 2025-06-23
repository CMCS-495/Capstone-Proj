#!/usr/bin/env python3
import argparse
from transformers import pipeline

def main():
    parser = argparse.ArgumentParser(description="LLM client using Hugging Face Transformers")
    parser.add_argument("prompt", help="Prompt string to send to the LLM")
    parser.add_argument(
        "--max_length",
        type=int,
        default=100,
        help="Maximum tokens to generate (default: 100)"
    )
    parser.add_argument(
        "--num_return_sequences",
        type=int,
        default=1,
        help="Number of responses to generate (default: 1)"
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Device ID for inference (e.g., 0 for GPU). If omitted, uses CPU."
    )
    args = parser.parse_args()

    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    llm = pipeline(
        "text-generation",
        model=model_name,
        device=args.device
    )

    outputs = llm(
        args.prompt,
        max_length=args.max_length,
        num_return_sequences=args.num_return_sequences
    )

    for out in outputs:
        print(out["generated_text"])

if __name__ == "__main__":
    main()
