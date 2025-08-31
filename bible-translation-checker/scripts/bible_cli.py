#!/usr/bin/env python3
"""
Bible Correction System - Command Line Interface

Provides command-line access to the Bible correction system for:
- Importing JSON files
- Scanning for errors
- Viewing statistics
- Exporting translations

Usage:
    python3 bible_cli.py [command] [options]
"""

import sys
import argparse
from pathlib import Path
from bible_correction_system import BibleDatabaseManager, ErrorDetectionEngine
import json

def import_json_file(db_manager, file_path, translation=None):
    """Import a JSON Bible file"""
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: File not found: {file_path}")
            return False
        
        print(f"Importing {path.name}...")
        
        def progress_callback(count, description):
            if count % 1000 == 0:
                print(f"  {count} {description}")
        
        result = db_manager.import_json_file(path, translation, progress_callback)
        
        print(f"✅ Import successful:")
        print(f"   Translation: {result['translation']}")
        print(f"   Total verses: {result['total_verses']}")
        print(f"   Books: {result['books']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def scan_translation(db_manager, translation):
    """Scan a translation for errors"""
    try:
        engine = ErrorDetectionEngine(db_manager)
        
        print(f"Scanning {translation} for errors...")
        
        def progress_callback(current, total, description):
            if current % 500 == 0:
                progress = (current / total) * 100
                print(f"  Progress: {progress:.1f}% - {description}")
        
        result = engine.scan_translation(translation, progress_callback)
        
        print(f"✅ Scan complete:")
        print(f"   Total verses: {result['total_verses']}")
        print(f"   Errors found: {result['errors_found']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return False

def show_statistics(db_manager):
    """Show database statistics"""
    try:
        print("\n📊 Database Statistics")
        print("=" * 50)
        
        # Translation statistics
        translations = db_manager.get_translations()
        print(f"Translations: {len(translations)}")
        
        total_verses = sum(t.get('total_verses', 0) for t in translations)
        total_errors = sum(t.get('error_count', 0) for t in translations)
        
        print(f"Total verses: {total_verses:,}")
        print(f"Total open errors: {total_errors:,}")
        
        if translations:
            print(f"\nTranslation Details:")
            for trans in translations:
                verses = trans.get('total_verses', 0)
                errors = trans.get('error_count', 0)
                print(f"  {trans['abbrev']}: {verses:,} verses, {errors} errors")
        
        # Error type statistics
        error_stats = db_manager.get_error_statistics()
        active_errors = [stat for stat in error_stats if stat['total_count'] > 0]
        
        if active_errors:
            print(f"\nError Type Statistics:")
            print("-" * 30)
            
            for stat in sorted(active_errors, key=lambda x: x['total_count'], reverse=True)[:10]:
                print(f"  {stat['error_code']}: {stat['total_count']} total, "
                      f"{stat['open_count']} open ({stat['severity']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
        return False

def export_translation(db_manager, translation, output_file, use_corrected=True):
    """Export a translation to JSON"""
    try:
        print(f"Exporting {translation}...")
        
        data = db_manager.export_translation(translation, use_corrected)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        verses_exported = sum(
            len(book['chapters'][ch]) 
            for book in data['books'].values() 
            for ch in book['chapters']
        )
        
        print(f"✅ Export successful:")
        print(f"   File: {output_file}")
        print(f"   Verses exported: {verses_exported:,}")
        print(f"   Used corrected text: {use_corrected}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

def list_translations(db_manager):
    """List all available translations"""
    try:
        translations = db_manager.get_translations()
        
        if not translations:
            print("No translations found in database.")
            return True
        
        print("\n📚 Available Translations")
        print("=" * 50)
        print(f"{'Abbrev':<6} {'Name':<25} {'Verses':<8} {'Errors':<8}")
        print("-" * 50)
        
        for trans in translations:
            abbrev = trans['abbrev']
            name = trans['full_name'][:25]
            verses = trans.get('total_verses', 0)
            errors = trans.get('error_count', 0)
            
            print(f"{abbrev:<6} {name:<25} {verses:<8} {errors:<8}")
        
        return True
        
    except Exception as e:
        print(f"❌ List failed: {e}")
        return False

def show_errors(db_manager, translation=None, error_type=None, limit=20):
    """Show error instances"""
    try:
        error_type_id = None
        if error_type:
            error_types = db_manager.get_error_types()
            error_type_obj = next((et for et in error_types if et['error_code'] == error_type), None)
            if error_type_obj:
                error_type_id = error_type_obj['id']
            else:
                print(f"Error: Unknown error type: {error_type}")
                return False
        
        errors = db_manager.get_error_instances(error_type_id=error_type_id)
        
        if translation:
            errors = [e for e in errors if e['translation'] == translation]
        
        if not errors:
            print("No errors found matching criteria.")
            return True
        
        print(f"\n⚠️  Error Instances (showing first {min(limit, len(errors))} of {len(errors)})")
        print("=" * 80)
        
        for i, error in enumerate(errors[:limit]):
            ref = f"{error['translation']} {error['book']} {error['chapter']}:{error['verse']}"
            print(f"{i+1:2}. {ref} - {error['error_code']} ({error['severity']})")
            print(f"    {error['error_text']}")
            print(f"    Status: {error['status']}")
            print()
        
        if len(errors) > limit:
            print(f"... and {len(errors) - limit} more errors")
        
        return True
        
    except Exception as e:
        print(f"❌ Show errors failed: {e}")
        return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Bible Correction System - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 bible_cli.py import KJV.json
  python3 bible_cli.py scan KJV
  python3 bible_cli.py stats
  python3 bible_cli.py export KJV KJV_corrected.json
  python3 bible_cli.py list
  python3 bible_cli.py errors --translation KJV --type NUMBERS_IN_TEXT
        """
    )
    
    parser.add_argument('--db', default='bible_correction.db',
                       help='Database file path (default: bible_correction.db)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import JSON Bible file')
    import_parser.add_argument('file', help='JSON file to import')
    import_parser.add_argument('--translation', help='Override translation abbreviation')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan translation for errors')
    scan_parser.add_argument('translation', help='Translation abbreviation to scan')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export translation to JSON')
    export_parser.add_argument('translation', help='Translation abbreviation to export')
    export_parser.add_argument('output', help='Output JSON file')
    export_parser.add_argument('--original', action='store_true',
                              help='Use original text instead of corrected')
    
    # List command
    subparsers.add_parser('list', help='List all translations')
    
    # Errors command
    errors_parser = subparsers.add_parser('errors', help='Show error instances')
    errors_parser.add_argument('--translation', help='Filter by translation')
    errors_parser.add_argument('--type', help='Filter by error type')
    errors_parser.add_argument('--limit', type=int, default=20, help='Limit results (default: 20)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize database
    try:
        db_manager = BibleDatabaseManager(args.db)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return 1
    
    success = False
    
    try:
        if args.command == 'import':
            success = import_json_file(db_manager, args.file, args.translation)
        
        elif args.command == 'scan':
            success = scan_translation(db_manager, args.translation)
        
        elif args.command == 'stats':
            success = show_statistics(db_manager)
        
        elif args.command == 'export':
            use_corrected = not args.original
            success = export_translation(db_manager, args.translation, args.output, use_corrected)
        
        elif args.command == 'list':
            success = list_translations(db_manager)
        
        elif args.command == 'errors':
            success = show_errors(db_manager, args.translation, args.type, args.limit)
        
        else:
            print(f"Unknown command: {args.command}")
            success = False
    
    finally:
        db_manager.close()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())