#!/usr/bin/env python3
"""
Local test script to validate the Deye SUN integration code.
This checks for syntax errors and basic import issues without Home Assistant.
"""

import ast
import sys
import json
from pathlib import Path

INTEGRATION_PATH = Path("custom_components/deye_sun")

def check_python_syntax(file_path: Path) -> tuple[bool, str]:
    """Check Python file for syntax errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def check_json_syntax(file_path: Path) -> tuple[bool, str]:
    """Check JSON file for syntax errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, "OK"
    except json.JSONDecodeError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def check_manifest(file_path: Path) -> tuple[bool, str]:
    """Check manifest.json for required fields."""
    required_fields = ["domain", "name", "version", "config_flow"]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        missing = [f for f in required_fields if f not in manifest]
        if missing:
            return False, f"Missing required fields: {missing}"
        
        return True, f"Domain: {manifest['domain']}, Version: {manifest['version']}"
    except Exception as e:
        return False, str(e)

def check_translations_match(strings_path: Path, translations_path: Path) -> tuple[bool, str]:
    """Check that translations have the same keys as strings.json."""
    try:
        with open(strings_path, 'r', encoding='utf-8') as f:
            strings = json.load(f)
        
        def get_keys(d, prefix=""):
            keys = set()
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.update(get_keys(v, full_key))
                else:
                    keys.add(full_key)
            return keys
        
        strings_keys = get_keys(strings)
        
        for trans_file in translations_path.glob("*.json"):
            with open(trans_file, 'r', encoding='utf-8') as f:
                trans = json.load(f)
            trans_keys = get_keys(trans)
            
            missing_in_trans = strings_keys - trans_keys
            extra_in_trans = trans_keys - strings_keys
            
            if missing_in_trans:
                return False, f"{trans_file.name}: Missing keys: {missing_in_trans}"
        
        return True, "All translations match strings.json"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("🔍 Deye SUN Integration Validation")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check Python files
    print("\n📄 Python Files:")
    py_files = list(INTEGRATION_PATH.glob("*.py"))
    for py_file in py_files:
        success, msg = check_python_syntax(py_file)
        status = "✅" if success else "❌"
        print(f"   {status} {py_file.name}: {msg}")
        if not success:
            errors.append(f"{py_file.name}: {msg}")
    
    # Check JSON files
    print("\n📄 JSON Files:")
    json_files = list(INTEGRATION_PATH.glob("*.json"))
    for json_file in json_files:
        success, msg = check_json_syntax(json_file)
        status = "✅" if success else "❌"
        print(f"   {status} {json_file.name}: {msg}")
        if not success:
            errors.append(f"{json_file.name}: {msg}")
    
    # Check translation files
    trans_path = INTEGRATION_PATH / "translations"
    if trans_path.exists():
        print("\n📄 Translation Files:")
        for trans_file in trans_path.glob("*.json"):
            success, msg = check_json_syntax(trans_file)
            status = "✅" if success else "❌"
            print(f"   {status} {trans_file.name}: {msg}")
            if not success:
                errors.append(f"translations/{trans_file.name}: {msg}")
    
    # Check manifest
    print("\n📦 Manifest Check:")
    manifest_path = INTEGRATION_PATH / "manifest.json"
    if manifest_path.exists():
        success, msg = check_manifest(manifest_path)
        status = "✅" if success else "❌"
        print(f"   {status} {msg}")
        if not success:
            errors.append(f"manifest.json: {msg}")
    
    # Check translation completeness
    print("\n🌐 Translation Completeness:")
    strings_path = INTEGRATION_PATH / "strings.json"
    if strings_path.exists() and trans_path.exists():
        success, msg = check_translations_match(strings_path, trans_path)
        status = "✅" if success else "⚠️"
        print(f"   {status} {msg}")
        if not success:
            warnings.append(msg)
    
    # Check for common issues in code
    print("\n🔬 Code Analysis:")
    
    # Check config_flow.py for OptionsFlow
    config_flow = INTEGRATION_PATH / "config_flow.py"
    if config_flow.exists():
        with open(config_flow, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_options_flow = "OptionsFlow" in content or "async_get_options_flow" in content
        status = "✅" if has_options_flow else "ℹ️"
        print(f"   {status} Options Flow: {'Implemented' if has_options_flow else 'Not implemented'}")
        
        has_domain = "domain=DOMAIN" in content
        status = "✅" if has_domain else "❌"
        print(f"   {status} ConfigFlow domain binding: {'Found' if has_domain else 'Missing'}")
        if not has_domain:
            errors.append("config_flow.py: Missing domain=DOMAIN in ConfigFlow class")
    
    # Check __init__.py
    init_file = INTEGRATION_PATH / "__init__.py"
    if init_file.exists():
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_setup_entry = "async_setup_entry" in content
        has_unload_entry = "async_unload_entry" in content
        
        status = "✅" if has_setup_entry else "❌"
        print(f"   {status} async_setup_entry: {'Found' if has_setup_entry else 'Missing'}")
        if not has_setup_entry:
            errors.append("__init__.py: Missing async_setup_entry")
        
        status = "✅" if has_unload_entry else "❌"
        print(f"   {status} async_unload_entry: {'Found' if has_unload_entry else 'Missing'}")
        if not has_unload_entry:
            errors.append("__init__.py: Missing async_unload_entry")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ VALIDATION FAILED - {len(errors)} error(s) found:")
        for err in errors:
            print(f"   • {err}")
        return 1
    elif warnings:
        print(f"⚠️  VALIDATION PASSED with {len(warnings)} warning(s):")
        for warn in warnings:
            print(f"   • {warn}")
        return 0
    else:
        print("✅ VALIDATION PASSED - Integration is ready!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
