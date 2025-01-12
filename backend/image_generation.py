import asyncio
import os
import re
from openai import AsyncOpenAI
from bs4 import BeautifulSoup


async def process_tasks(prompts):
    tasks = [generate_image(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"An exception occurred: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)

    return processed_results


async def generate_image(prompt):
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    image_params = {
        "model": "dall-e-3",
        "quality": "standard",
        "style": "natural",
        "n": 1,
        "size": "1024x1024",
        "prompt": prompt,
    }
    res = await client.images.generate(**image_params)
    return res.data[0].url


def extract_dimensions(url):
    # Regular expression to match numbers in the format '300x200'
    matches = re.findall(r"(\d+)x(\d+)", url)

    if matches:
        width, height = matches[0]  # Extract the first match
        width = int(width)
        height = int(height)
        return (width, height)
    else:
        return (100, 100)


async def generate_images(code):
    # Find all images and extract their alt texts
    soup = BeautifulSoup(code, "html.parser")
    images = soup.find_all("img")
    alts = [img.get("alt", None) for img in images]

    # Exclude images with no alt text
    alts = [alt for alt in alts if alt is not None]

    # Remove duplicates
    prompts = list(set(alts))

    # Generate images
    results = await process_tasks(prompts)

    # Create a dict mapping alt text to image URL
    mapped_image_urls = dict(zip(prompts, results))

    # Replace alt text with image URLs
    for img in images:
        new_url = mapped_image_urls[img.get("alt")]

        if new_url:
            # Set width and height attributes
            width, height = extract_dimensions(img["src"])
            img["width"] = width
            img["height"] = height
            # Replace img['src'] with the mapped image URL
            img["src"] = new_url
        else:
            print("Image generation failed for alt text:" + img.get("alt"))

    # Return the modified HTML
    return str(soup)
