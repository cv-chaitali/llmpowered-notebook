#!/usr/bin/env python3
"""Test script to download and test Qwen model"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

print("Starting model download test...")
print("This will download ~400MB on first run")
print()

try:
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    
    print(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    print("✓ Tokenizer loaded successfully")
    
    print(f"Loading model (this may take a few minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="cpu",
        low_cpu_mem_usage=True
    )
    print("✓ Model loaded successfully")
    
    # Test generation
    print("\nTesting text generation...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one sentence."}
    ]
    
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer([text], return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=50)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    print(f"Generated text: {result}")
    print("\n✓ All tests passed! Model is working correctly.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check internet connection")
    print("2. Try: pip install --upgrade transformers torch")
    print("3. Check disk space (~400MB needed)")
