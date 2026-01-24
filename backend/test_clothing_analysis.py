"""
Test script to analyze all clothing images in the dataset.
Outputs structured JSON for each image.
"""

import os
import sys
import json
import cv2
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.cloth_analysis.schemas import ClothInput
from app.cloth_analysis.service import analyze_clothing


def format_output(image_name: str, result) -> dict:
    """Format analysis result to the required JSON structure."""
    if not result.success or result.features is None:
        return {
            "image": image_name,
            "error": result.error or "Analysis failed",
            "color": None,
            "design": None,
            "gender": None,
            "category": None,
            "weather": None,
            "style": None,
            "confidence": 0.0,
            "fabric": None,
            "formality_level": None
        }
    
    features = result.features
    
    # Get dominant color name (first color with highest percentage)
    dominant_color = features.dominant_colors[0].name if features.dominant_colors else "Unknown"
    
    # Format fabric (null if unknown)
    fabric = features.fabric.value if features.fabric.value != "unknown" else None
    
    return {
        "image": image_name,
        "color": dominant_color.replace("_", " ").title(),
        "design": features.design_pattern.value.replace("_", " ").title(),
        "gender": features.gender.value.title(),
        "category": features.category.value.replace("_", " ").title(),
        "weather": features.weather.value.replace("_", " ").title(),
        "style": features.style.value.title(),
        "confidence": round(features.overall_confidence, 2),
        "fabric": fabric.title() if fabric else None,
        "formality_level": features.formality_level
    }


async def analyze_image(image_path: str) -> dict:
    """Analyze a single clothing image."""
    import base64
    
    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    # Create input
    input_data = ClothInput(image_base64=image_base64)
    
    # Analyze (without CLIP for faster testing)
    result = await analyze_clothing(input_data, use_clip=False)
    
    return result


async def main():
    """Main function to analyze all clothing images."""
    # Path to dataset
    dataset_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "clothing_dataset"
    )
    
    # Get all PNG images
    images = sorted([f for f in os.listdir(dataset_path) if f.endswith(".png")])
    
    if not images:
        print("No PNG images found in dataset folder")
        return
    
    print(f"\n{'='*60}")
    print(f"CLOTHING ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Found {len(images)} images to analyze\n")
    
    all_results = []
    
    for image_name in images:
        image_path = os.path.join(dataset_path, image_name)
        
        print(f"Analyzing: {image_name}...")
        
        try:
            result = await analyze_image(image_path)
            formatted = format_output(image_name, result)
            all_results.append(formatted)
            
            # Print individual result
            print(json.dumps(formatted, indent=2))
            print(f"Processing time: {result.processing_time_ms:.2f}ms")
            print("-" * 40)
            
        except Exception as e:
            print(f"Error analyzing {image_name}: {e}")
            all_results.append({
                "image": image_name,
                "error": str(e)
            })
            print("-" * 40)
    
    # Print summary
    print(f"\n{'='*60}")
    print("ALL RESULTS (JSON Array)")
    print(f"{'='*60}")
    print(json.dumps(all_results, indent=2))
    
    # Save results to file
    output_path = os.path.join(dataset_path, "analysis_results.json")
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
