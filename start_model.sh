#!/bin/bash

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo "Warning: HF_TOKEN is not set. You may encounter issues accessing Gemma models."
fi

# Setup Hugging Face credentials if token is provided
if [ ! -z "$HF_TOKEN" ]; then
    # Configure huggingface-cli
    huggingface-cli login --token $HF_TOKEN
fi

# Get MODEL_ID from environment variable
MODEL_ID=${MODEL_ID:-"meta-llama/Meta-Llama-3-8B-Instruct"}
echo "Using model: $MODEL_ID"

# Launch the model API server
python -c "
from transformers import AutoTokenizer, pipeline, AutoModelForCausalLM
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import torch
import uvicorn
import json
import asyncio
import os
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime

app = FastAPI(title='LLM API')

print('Loading model and tokenizer...')
model_id = os.environ.get('MODEL_ID', 'meta-llama/Meta-Llama-3-8B-Instruct')
print(f'Using model: {model_id}')

try:
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        low_cpu_mem_usage=True,
        device_map='auto',
        torch_dtype=torch.float16
    )
    print(f'Successfully loaded model and tokenizer')
except Exception as e:
    print(f'Error loading model: {str(e)}')
    raise

# Define input schema
class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class ModelInfo(BaseModel):
    id: str
    object: str = 'model'
    created: int
    owned_by: str = 'meta'

@app.get('/v1/models')
async def list_models():
    models = [
        ModelInfo(
            id=model_id,
            created=int(datetime.datetime.now().timestamp()),
        )
    ]
    return {
        'object': 'list',
        'data': models
    }

def generate_streaming_response(prompt, max_tokens, temperature):
    inputs = tokenizer(prompt, return_tensors='pt').to(model.device)
    
    generate_kwargs = {
        'max_new_tokens': max_tokens,
        'temperature': temperature,
        'top_p': 0.95,
        'do_sample': temperature > 0,
    }
    
    streamer = TransformersStreamingGenerator(
        model=model,
        tokenizer=tokenizer,
        **generate_kwargs
    )
    
    return streamer.generate(inputs.input_ids)

@app.post('/v1/completions')
async def create_completion(request: CompletionRequest):
    try:
        if request.stream:
            async def streaming_response():
                for response in generate_streaming_response(
                    request.prompt,
                    request.max_tokens,
                    request.temperature
                ):
                    data = {
                        'id': f'cmpl-{datetime.datetime.now().timestamp()}',
                        'object': 'text_completion',
                        'created': int(datetime.datetime.now().timestamp()),
                        'model': request.model,
                        'choices': [
                            {
                                'text': response,
                                'index': 0,
                                'finish_reason': 'stop' if response == '' else None
                            }
                        ],
                    }
                    yield f'data: {json.dumps(data)}\n\n'
                yield 'data: [DONE]\n\n'
            
            return StreamingResponse(streaming_response(), media_type='text/event-stream')
        else:
            inputs = tokenizer(request.prompt, return_tensors='pt').to(model.device)
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=0.95,
                do_sample=request.temperature > 0,
            )
            
            output_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            
            return {
                'id': f'cmpl-{datetime.datetime.now().timestamp()}',
                'object': 'text_completion',
                'created': int(datetime.datetime.now().timestamp()),
                'model': request.model,
                'choices': [
                    {
                        'text': output_text,
                        'index': 0,
                        'finish_reason': 'stop'
                    }
                ],
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

@app.post('/v1/chat/completions')
async def create_chat_completion(request: ChatCompletionRequest):
    try:
        chat_template = tokenizer.chat_template
        prompt = tokenizer.apply_chat_template(request.messages, tokenize=False)
        
        if request.stream:
            async def streaming_response():
                for response in generate_streaming_response(
                    prompt,
                    request.max_tokens,
                    request.temperature
                ):
                    data = {
                        'id': f'chatcmpl-{datetime.datetime.now().timestamp()}',
                        'object': 'chat.completion.chunk',
                        'created': int(datetime.datetime.now().timestamp()),
                        'model': request.model,
                        'choices': [
                            {
                                'delta': {'content': response},
                                'index': 0,
                                'finish_reason': 'stop' if response == '' else None
                            }
                        ],
                    }
                    yield f'data: {json.dumps(data)}\n\n'
                yield 'data: [DONE]\n\n'
            
            return StreamingResponse(streaming_response(), media_type='text/event-stream')
        else:
            inputs = tokenizer(prompt, return_tensors='pt').to(model.device)
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=0.95,
                do_sample=request.temperature > 0,
            )
            
            output_text = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            
            return {
                'id': f'chatcmpl-{datetime.datetime.now().timestamp()}',
                'object': 'chat.completion',
                'created': int(datetime.datetime.now().timestamp()),
                'model': request.model,
                'choices': [
                    {
                        'message': {'role': 'assistant', 'content': output_text},
                        'index': 0,
                        'finish_reason': 'stop'
                    }
                ],
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': str(e)}
        )

@app.get('/health')
async def health_check():
    return {'status': 'ok', 'message': 'RecruitPro AI API is operational'}

if __name__ == '__main__':
    from transformers_stream_generator import TransformersStreamingGenerator
    uvicorn.run(app, host='0.0.0.0', port=8000)
" 