"""Read and print all parameters from the downloaded YOLO model."""
import json
import torch
from ultralytics import YOLO

model = YOLO("models/best.pt")
m = model.model

print("=== MODEL PARAMETERS ===")
print(f"Task:           {model.task}")
print(f"Architecture:   {type(m).__name__}")

total_params = sum(p.numel() for p in m.parameters())
trainable = sum(p.numel() for p in m.parameters() if p.requires_grad)
print(f"Total params:   {total_params:,}")
print(f"Trainable:      {trainable:,}")

names = model.names
print(f"Num classes:    {len(names)}")
print(f"Classes:        {json.dumps(names, indent=2)}")

ckpt = model.ckpt or {}
print(f"\nEpochs trained: {ckpt.get('epoch', 'unknown')}")
print(f"Best fitness:   {ckpt.get('best_fitness', 'unknown')}")

train_args = ckpt.get("train_args", {})
if train_args:
    print(f"\n--- Training args ---")
    for k, v in train_args.items():
        print(f"  {k}: {v}")

# Model yaml
if hasattr(m, "yaml"):
    print(f"\n--- Model YAML ---")
    print(json.dumps(m.yaml, indent=2, default=str))
