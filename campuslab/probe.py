"""Runs inside the explicitly selected interpreter. Fixed read-only observations only."""
import importlib.metadata
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['python-basics','local-qwen'], default='python-basics')
    parser.add_argument('--model-dir')
    parser.add_argument('--infer', action='store_true')
    args=parser.parse_args()
    packages = {}
    names = ('requests',) if args.scenario == 'python-basics' else ('torch','transformers')
    for name in names:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    try:
        program = 'import requests; print("OK")' if args.scenario == 'python-basics' else 'import torch, transformers; print("OK")'
        run = subprocess.run([sys.executable, '-B', '-I', '-c', program],
                             capture_output=True, timeout=20, text=True, encoding='utf-8', errors='replace')
        verification = dict(returncode=run.returncode, stdout=run.stdout[-3000:], error=run.stderr[-3000:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        verification = dict(returncode=None, stdout='', error=type(exc).__name__)
    result = dict(actual=sys.executable, os=platform.system(), python=platform.python_version(),
                  packages=packages, verification=verification)
    if args.scenario == 'local-qwen':
        result['model'],result['resources'] = local_model(args.model_dir, args.infer)
    print(json.dumps(result, ensure_ascii=True))


def local_model(directory, infer):
    model_info = dict(directory=directory, weights_sha256=None, inference=None)
    resources = dict(ram_bytes=None, gpu=None, vram_bytes=None, collection='read-only; unknown fields remain null')
    if platform.system() == 'Windows':
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)] + [(name,ctypes.c_ulonglong) for name in ('total','available','page','page_available','virtual','virtual_available','extended')]
        mem=Memory(); mem.length=ctypes.sizeof(mem)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            resources['ram_bytes']=mem.total
    if not directory or not (Path(directory)/'model.safetensors').is_file():
        return model_info,resources
    weights=Path(directory)/'model.safetensors'
    h=hashlib.sha256()
    with weights.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    model_info['weights_sha256']=h.hexdigest().upper()
    if not infer:
        return model_info,resources
    outcome=dict(offline=True,local=True,output='',ended_with_eos=False,device='',error='')
    model_info['inference']=outcome
    if model_info['weights_sha256'] != 'FDF756FA7FCBE7404D5C60E26BFF1A0C8B8AA1F72CED49E7DD0210FE288FB7FE':
        outcome['error']='weights_digest_mismatch'; return model_info,resources
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',HF_HUB_DISABLE_IMPLICIT_TOKEN='1',USE_TF='0')
    def offline(*args,**kwargs):
        raise RuntimeError('Network disabled in local inference process')
    socket.socket.connect=offline; socket.socket.connect_ex=offline
    try:
        import torch
        from transformers import AutoModelForCausalLM,AutoTokenizer
        device='cuda' if torch.cuda.is_available() else 'cpu'
        outcome['device']=device
        if device == 'cuda':
            resources.update(gpu=torch.cuda.get_device_name(0),vram_bytes=torch.cuda.get_device_properties(0).total_memory)
        tokenizer=AutoTokenizer.from_pretrained(directory,local_files_only=True,trust_remote_code=False)
        model=AutoModelForCausalLM.from_pretrained(directory,local_files_only=True,trust_remote_code=False,
                                                  use_safetensors=True,dtype=torch.float16 if device=='cuda' else torch.float32).to(device).eval()
        text=tokenizer.apply_chat_template([{'role':'user','content':'计算1+1，只输出答案，不要解释。'}],tokenize=False,add_generation_prompt=True)
        inputs=tokenizer(text,return_tensors='pt').to(device)
        with torch.inference_mode():
            result=model.generate(**inputs,max_new_tokens=32,do_sample=False,pad_token_id=tokenizer.eos_token_id)
        tokens=result[0,inputs.input_ids.shape[-1]:]
        outcome['output']=tokenizer.decode(tokens,skip_special_tokens=True)
        outcome['ended_with_eos']=bool(tokens.numel() and tokens[-1].item()==tokenizer.eos_token_id)
    except Exception as exc:
        outcome['error']=type(exc).__name__
    return model_info,resources


if __name__ == '__main__':
    main()
