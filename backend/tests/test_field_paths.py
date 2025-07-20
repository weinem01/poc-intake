#!/usr/bin/env python3
"""
Test script to debug field path generation for IntakeDemographics
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.models.intake_schemas import IntakeDemographics

def test_field_path_generation():
    """Test what field paths are generated from the schema"""
    
    # Get the model's JSON schema
    schema = IntakeDemographics.model_json_schema()
    print("=== IntakeDemographics Schema ===")
    print(f"Schema keys: {list(schema.keys())}")
    
    properties = schema.get("properties", {})
    print(f"\nTop-level properties: {list(properties.keys())}")
    
    # Test the field path extraction logic
    def extract_field_paths(properties: dict, prefix: str = "") -> list:
        """Recursively extract all field paths from schema properties"""
        paths = []
        
        for field_name, field_info in properties.items():
            # Skip system fields
            if field_name in ["isComplete"]:
                continue
                
            current_path = f"{prefix}.{field_name}" if prefix else field_name
            field_type = field_info.get("type", "unknown")
            
            print(f"Processing field: {current_path}, type: {field_type}")
            
            if field_type == "object":
                # Add the object itself
                paths.append(current_path)
                # Recursively add nested fields
                nested_props = field_info.get("properties", {})
                if nested_props:
                    print(f"  Object {current_path} has nested properties: {list(nested_props.keys())}")
                    nested_paths = extract_field_paths(nested_props, current_path)
                    paths.extend(nested_paths)
                else:
                    print(f"  Object {current_path} has no nested properties")
            elif field_type == "array":
                # Add array fields
                paths.append(current_path)
                # If array of objects, add nested paths
                items = field_info.get("items", {})
                if "properties" in items:
                    nested_props = items.get("properties", {})
                    print(f"  Array {current_path} has nested properties: {list(nested_props.keys())}")
                    nested_paths = extract_field_paths(nested_props, current_path)
                    paths.extend(nested_paths)
            else:
                # Simple field
                paths.append(current_path)
        
        return paths
    
    all_paths = extract_field_paths(properties)
    
    print(f"\n=== Generated Field Paths ===")
    for i, path in enumerate(all_paths, 1):
        print(f"{i:2d}. {path}")
    
    print(f"\nTotal paths: {len(all_paths)}")
    
    # Check specifically for maritalStatus and employmentStatus
    marital_paths = [p for p in all_paths if "marital" in p.lower()]
    employment_paths = [p for p in all_paths if "employment" in p.lower()]
    
    print(f"\nMarital status paths: {marital_paths}")
    print(f"Employment status paths: {employment_paths}")

if __name__ == "__main__":
    test_field_path_generation()