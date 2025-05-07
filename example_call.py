#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example API Client - Demonstrates how to call the Image Generation Service API

This script shows how to use all the main endpoints of the remote image generation service:
1. Root endpoint: Check if service is running
2. Health check: Check service health status
3. Image generation: Generate an image using a prompt and save it
4. Async image generation: Start an async generation task
5. Task status: Check the status of an async task
6. Download result: Download the result of a completed task
7. List tasks: List all tasks in the system
"""

import requests
import base64
from PIL import Image
from io import BytesIO
import os
import time
import argparse
import json

# Default server configuration (can be modified via command line arguments)
DEFAULT_SERVER_HOST = "127.0.0.1"  # Replace with your server IP address
DEFAULT_SERVER_PORT = 8000  # Modify according to your service configuration

def check_service_status(base_url):
    """Check service status (root endpoint)
    
    Args:
        base_url (str): Base URL of the service
        
    Returns:
        dict: Service status information
    """
    print("Checking service status...")
    response = requests.get(f"{base_url}/")
    if response.status_code == 200:
        data = response.json()
        print(f"Service status: {data}")
        return data
    else:
        print(f"Could not connect to service, status code: {response.status_code}")
        return None

def check_health(base_url):
    """Check service health
    
    Args:
        base_url (str): Base URL of the service
        
    Returns:
        dict: Health status information
    """
    print("Checking service health...")
    response = requests.get(f"{base_url}/api/health")
    if response.status_code == 200:
        data = response.json()
        print(f"Health status: {data}")
        return data
    else:
        print(f"Health check failed, status code: {response.status_code}")
        return None

def generate_and_save_image(base_url, prompt, seed=None, output_dir="imgs"):
    """Generate and save image (synchronous)
    
    Args:
        base_url (str): Base URL of the service
        prompt (str): Image generation prompt
        seed (int, optional): Random seed for reproducibility
        output_dir (str, optional): Directory to save the image
        
    Returns:
        str: Path to the saved image file, or None if failed
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Prepare request data
    request_data = {
        "prompt": prompt
    }
    if seed is not None:
        request_data["seed"] = seed
    
    print(f"Generating image with prompt: '{prompt}'...")
    if seed is not None:
        print(f"Using seed: {seed}")
    
    # Send request
    try:
        response = requests.post(f"{base_url}/api/generate", json=request_data)
        response.raise_for_status()  # Raises exception for non-200 status codes
        
        data = response.json()
        
        # Decode and save image
        image_data = base64.b64decode(data["image_base64"])
        image = Image.open(BytesIO(image_data))
        
        # Generate filename
        timestamp = int(time.time())
        seed_value = data.get("seed", "random")
        filename = f"image_{timestamp}_{seed_value}.png"
        file_path = os.path.join(output_dir, filename)
        
        # Save image
        image.save(file_path)
        print(f"Image saved to: {file_path}")
        
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Failed to process image: {e}")
        return None

def create_async_task(base_url, prompt, seed=None):
    """Create an asynchronous image generation task
    
    Args:
        base_url (str): Base URL of the service
        prompt (str): Image generation prompt
        seed (int, optional): Random seed for reproducibility
        
    Returns:
        str: Task ID if successful, None otherwise
    """
    # Prepare request data
    request_data = {
        "prompt": prompt
    }
    if seed is not None:
        request_data["seed"] = seed
    
    print(f"Creating async task with prompt: '{prompt}'...")
    if seed is not None:
        print(f"Using seed: {seed}")
    
    try:
        response = requests.post(f"{base_url}/api/generate-async", json=request_data)
        response.raise_for_status()
        
        data = response.json()
        task_id = data.get("task_id")
        
        if task_id:
            print(f"Async task created with ID: {task_id}")
            # Save task ID to temp file for convenience
            with open("temp_task_id.txt", "w") as f:
                f.write(task_id)
            return task_id
        else:
            print("Failed to get task ID from response")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def check_task_status(base_url, task_id):
    """Check the status of an async task
    
    Args:
        base_url (str): Base URL of the service
        task_id (str): Task ID to check
        
    Returns:
        dict: Task status information
    """
    print(f"Checking status for task: {task_id}")
    try:
        response = requests.get(f"{base_url}/api/task/{task_id}")
        response.raise_for_status()
        
        data = response.json()
        status = data.get("status", "unknown")
        progress = data.get("progress", 0)
        total_steps = data.get("total_steps", 1)
        
        progress_percent = (progress / max(1, total_steps)) * 100
        print(f"Status: {status}, Progress: {progress}/{total_steps} ({progress_percent:.1f}%)")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def wait_for_task_completion(base_url, task_id, max_polls=30, poll_interval=2):
    """Wait for a task to complete, polling at regular intervals
    
    Args:
        base_url (str): Base URL of the service
        task_id (str): Task ID to check
        max_polls (int): Maximum number of status checks
        poll_interval (int): Time between status checks in seconds
        
    Returns:
        dict: Final task status or None if timed out
    """
    print(f"Waiting for task {task_id} to complete...")
    
    for i in range(max_polls):
        status_data = check_task_status(base_url, task_id)
        
        if not status_data:
            print("Failed to get task status")
            return None
        
        if status_data.get("status") in ["completed", "failed"]:
            print(f"Task {status_data.get('status')}")
            if status_data.get("status") == "failed" and status_data.get("error"):
                print(f"Error: {status_data.get('error')}")
            return status_data
        
        print(f"Waiting {poll_interval} seconds before next check...")
        time.sleep(poll_interval)
    
    print(f"Task did not complete within {max_polls * poll_interval} seconds")
    return None

def get_and_save_result(base_url, task_id, output_dir="imgs"):
    """Get and save the result of a completed task
    
    Args:
        base_url (str): Base URL of the service
        task_id (str): Task ID to get result for
        output_dir (str): Directory to save the image
        
    Returns:
        str: Path to saved image or None if failed
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        print(f"Getting result for task: {task_id}")
        response = requests.get(f"{base_url}/api/result/{task_id}")
        response.raise_for_status()
        
        data = response.json()
        
        if "image_base64" not in data:
            print("No image data in response")
            return None
        
        # Decode and save image
        image_data = base64.b64decode(data["image_base64"])
        image = Image.open(BytesIO(image_data))
        
        # Generate filename
        timestamp = int(time.time())
        seed_value = data.get("seed", "random")
        filename = f"async_image_{timestamp}_{seed_value}.png"
        file_path = os.path.join(output_dir, filename)
        
        # Save image
        image.save(file_path)
        print(f"Async generated image saved to: {file_path}")
        
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Failed to process image: {e}")
        return None

def list_tasks(base_url):
    """List all tasks in the system
    
    Args:
        base_url (str): Base URL of the service
        
    Returns:
        list: List of tasks
    """
    try:
        print("Getting task list...")
        response = requests.get(f"{base_url}/api/tasks")
        response.raise_for_status()
        
        data = response.json()
        tasks = data.get("tasks", [])
        
        if tasks:
            print(f"Found {len(tasks)} tasks:")
            for task in tasks:
                status = task.get("status", "unknown")
                prompt = task.get("prompt", "No prompt")
                created_at = task.get("created_at", "Unknown time")
                print(f"- ID: {task.get('id')}, Status: {status}, Prompt: {prompt}, Created at: {created_at}")
        else:
            print("No tasks found")
        
        return tasks
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def async_workflow(base_url, prompt, seed=None, output_dir="imgs"):
    """Complete async workflow: create task, wait for completion, download result
    
    Args:
        base_url (str): Base URL of the service
        prompt (str): Image generation prompt
        seed (int, optional): Random seed for reproducibility
        output_dir (str): Directory to save the image
        
    Returns:
        str: Path to saved image or None if failed
    """
    # Create task
    task_id = create_async_task(base_url, prompt, seed)
    if not task_id:
        return None
    
    # Wait for task to complete
    final_status = wait_for_task_completion(base_url, task_id)
    if not final_status or final_status.get("status") != "completed":
        return None
    
    # Get and save result
    return get_and_save_result(base_url, task_id, output_dir)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Image Generation Service API Example Client')
    parser.add_argument('--host', default=DEFAULT_SERVER_HOST, help='Server host address')
    parser.add_argument('--port', type=int, default=DEFAULT_SERVER_PORT, help='Server port')
    parser.add_argument('--prompt', default="A cute cat, lay in the bed.", help='Image generation prompt')
    parser.add_argument('--seed', type=int, help='Random seed (optional)')
    parser.add_argument('--output-dir', default="imgs", help='Directory to save images')
    parser.add_argument('--mode', choices=['sync', 'async', 'status', 'result', 'list', 'workflow'],
                      default='sync', help='Operation mode')
    parser.add_argument('--task-id', help='Task ID for status/result operations')
    
    args = parser.parse_args()
    
    # Build base URL
    base_url = f"http://{args.host}:{args.port}"
    
    print(f"Using service URL: {base_url}")
    
    # Check service status
    service_status = check_service_status(base_url)
    if not service_status or service_status.get("status") != "running":
        print("Service is not running, exiting")
        return
    
    # Check service health
    health_status = check_health(base_url)
    if not health_status or health_status.get("status") != "ok":
        print("Service health check failed, exiting")
        return
    
    # Perform requested operation
    if args.mode == 'sync':
        # Generate and save image (synchronous)
        generate_and_save_image(base_url, args.prompt, args.seed, args.output_dir)
    
    elif args.mode == 'async':
        # Create async task
        create_async_task(base_url, args.prompt, args.seed)
    
    elif args.mode == 'status':
        # Check task status
        if not args.task_id:
            # Try to read from temp file
            try:
                with open("temp_task_id.txt", "r") as f:
                    task_id = f.read().strip()
                    print(f"Using task ID from file: {task_id}")
            except FileNotFoundError:
                print("No task ID provided and could not read from file")
                return
        else:
            task_id = args.task_id
        
        check_task_status(base_url, task_id)
    
    elif args.mode == 'result':
        # Get and save task result
        if not args.task_id:
            # Try to read from temp file
            try:
                with open("temp_task_id.txt", "r") as f:
                    task_id = f.read().strip()
                    print(f"Using task ID from file: {task_id}")
            except FileNotFoundError:
                print("No task ID provided and could not read from file")
                return
        else:
            task_id = args.task_id
        
        get_and_save_result(base_url, task_id, args.output_dir)
    
    elif args.mode == 'list':
        # List all tasks
        list_tasks(base_url)
    
    elif args.mode == 'workflow':
        # Complete async workflow
        async_workflow(base_url, args.prompt, args.seed, args.output_dir)

if __name__ == "__main__":
    main() 