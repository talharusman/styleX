"""
Enhanced test script to analyze clothing images with detailed output.
Shows color palette and all confidence scores.
"""

import os
import sys
import json
import cv2
import asyncio
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.cloth_analysis.schemas import ClothInput
from app.cloth_analysis.service import ClothAnalysisService


async def analyze_with_details(image_path: str):
    """Analyze image and return detailed results."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    input_data = ClothInput(image_base64=image_base64)
    
    service = ClothAnalysisService()
    result = await service.analyze(input_data, use_clip=True)  # Enable CLIP
    
    return result


def format_detailed_output(image_name: str, result) -> dict:
    """Format with full details including all colors."""
    if not result.success or result.features is None:
        return {"image": image_name, "error": result.error}
    
    f = result.features
    
    # Get all colors with details
    colors = []
    for c in f.dominant_colors:
        colors.append({
            "name": c.name.replace("_", " ").title(),
            "hex": c.hex_code,
            "rgb": c.rgb,
            "percentage": c.percentage
        })
    
    return {
        "image": image_name,
        "processing_time_ms": result.processing_time_ms,
        "overall_confidence": round(f.overall_confidence, 4),
        "features": {
            "colors": colors,
            "dominant_color": colors[0]["name"] if colors else "Unknown",
            "design": {
                "pattern": f.design_pattern.value.replace("_", " ").title(),
                "confidence": round(f.design_confidence, 4)
            },
            "category": {
                "type": f.category.value.replace("_", " ").title(),
                "confidence": round(f.category_confidence, 4)
            },
            "weather": {
                "season": f.weather.value.replace("_", " ").title(),
                "confidence": round(f.weather_confidence, 4)
            },
            "style": {
                "label": f.style.value.title(),
                "confidence": round(f.style_confidence, 4)
            },
            "fabric": {
                "type": f.fabric.value.title() if f.fabric.value != "unknown" else None,
                "confidence": round(f.fabric_confidence, 4)
            },
            "formality": {
                "level": f.formality_level,
                "confidence": round(f.formality_confidence, 4)
            }
        },
        "simplified_output": {
            "color": colors[0]["name"] if colors else "Unknown",
            "design": f.design_pattern.value.replace("_", " ").title(),
            "category": f.category.value.replace("_", " ").title(),
            "weather": f.weather.value.replace("_", " ").title(),
            "style": f.style.value.title(),
            "confidence": round(f.overall_confidence, 2),
            "fabric": f.fabric.value.title() if f.fabric.value != "unknown" else None,
            "formality_level": f.formality_level
        }
    }


async def main():
    """Analyze all images with detailed output."""
    dataset_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data", "clothing_dataset"
    )
    
    images = sorted([f for f in os.listdir(dataset_path) if f.endswith(".png")])
    
    print("\n" + "=" * 70)
    print("DETAILED CLOTHING ANALYSIS")
    print("=" * 70)
    print(f"Analyzing {len(images)} images...\n")
    
    all_results = []
    simplified_results = []
    
    for image_name in images:
        image_path = os.path.join(dataset_path, image_name)
        print(f"\n--- {image_name} ---")
        
        result = await analyze_with_details(image_path)
        detailed = format_detailed_output(image_name, result)
        
        all_results.append(detailed)
        
        if "simplified_output" in detailed:
            simplified_results.append({
                "image": image_name,
                **detailed["simplified_output"]
            })
            
            # Print summary
            s = detailed["simplified_output"]
            colors = detailed.get("features", {}).get("colors", [])
            
            print(f"  Color: {s['color']}")
            if len(colors) > 1:
                print(f"  Color palette: {', '.join([c['name'] for c in colors[:3]])}")
            print(f"  Design: {s['design']}")
            print(f"  Category: {s['category']}")
            print(f"  Style: {s['style']}")
            print(f"  Weather: {s['weather']}")
            print(f"  Formality: {s['formality_level']}/5")
            print(f"  Confidence: {s['confidence']:.0%}")
    
    # Final JSON outputs
    print("\n" + "=" * 70)
    print("SIMPLIFIED JSON OUTPUT (As requested)")
    print("=" * 70)
    print(json.dumps(simplified_results, indent=2))
    
    # Save detailed results
    with open(os.path.join(dataset_path, "detailed_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    
    with open(os.path.join(dataset_path, "simplified_results.json"), "w") as f:
        json.dump(simplified_results, f, indent=2)
    
    print(f"\nResults saved to data/clothing_dataset/")


if __name__ == "__main__":
    asyncio.run(main())
