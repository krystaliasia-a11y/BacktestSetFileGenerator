import csv
import os
import sys
import json
import random

def load_config(config_filename='config.json'):
    """Load configuration from JSON file"""
    if not os.path.exists(config_filename):
        print(f"Error: Could not find '{config_filename}'. Please create it in the same directory.")
        print("\nExample config.json:")
        print('{')
        print('    "csv_file": "pair_data.csv",')
        print('    "template_pattern": "SRM_v6.0_AlgoX_REAL-{pairName}-{timeFrame}-{nextYear}1231-{nextYear}0101-TEP{TepVar}_TBBB{year}.set",')
        print('    "tep_var": "0",')
        print('    "timeFrame": "H1",')
        print('    "magic_number_start": null,')
        print('    "output_dir": "output"')
        print('}')
        sys.exit(1)
    
    try:
        with open(config_filename, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

def find_template_file():
    """Find the single .set template file in current directory (excluding output folder)"""
    # Only look in current directory, not subdirectories
    set_files = [f for f in os.listdir('.') if f.endswith('.set') and os.path.isfile(f)]
    
    # Filter out files that look like output files (contain TBBB pattern)
    # to avoid accidentally using a generated file as a template
    potential_templates = [f for f in set_files if 'TBBB' not in f]
    
    if len(potential_templates) == 1:
        return potential_templates[0]
    elif len(potential_templates) == 0:
        # Fallback: if no clear template, just take any .set file in root
        if len(set_files) == 1:
            return set_files[0]
        elif len(set_files) == 0:
            print("Error: No .set template file found in current directory.")
            sys.exit(1)
        else:
            print(f"Warning: Multiple .set files found ({len(set_files)}). Using the first one: {set_files[0]}")
            return set_files[0]
    else:
        print(f"Warning: Multiple potential template files found ({len(potential_templates)}). Using: {potential_templates[0]}")
        return potential_templates[0]

def calculate_next_year(year_str):
    """Calculate next year from current year string"""
    try:
        current_year = int(year_str)
        next_year = current_year + 1
        return str(next_year)
    except ValueError:
        print(f"Warning: Invalid year format '{year_str}', using same year")
        return year_str

def main():
    # 1. Load configuration
    config = load_config()
    
    csv_filename = config.get('csv_file', 'pair_data.csv')
    template_pattern = config.get('template_pattern', 'SRM_v6.0_AlgoX_REAL-{pairName}-{timeFrame}-{nextYear}1231-{nextYear}0101-TEP{TepVar}_TBBB{year}.set')
    tep_var = str(config.get('tep_var', '0'))
    time_frame = str(config.get('timeFrame', 'H1'))
    magic_number_start = config.get('magic_number_start', None)
    output_dir = config.get('output_dir', 'output')
    
    print("=" * 50)
    print("Configuration Loaded:")
    print(f"  CSV File: {csv_filename}")
    print(f"  Template Pattern: {template_pattern}")
    print(f"  TepVar: {tep_var}")
    print(f"  TimeFrame: {time_frame}")
    print(f"  Output Directory: {output_dir}")
    print("=" * 50)
    
    # 2. Create Output Directory if it doesn't exist
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory ready: ./{output_dir}/")
    except Exception as e:
        print(f"Error creating output directory: {e}")
        sys.exit(1)
    
    # 3. Find template file (in current directory, NOT output directory)
    actual_template_filename = find_template_file()
    print(f"Using template file: {actual_template_filename}")
    
    # 4. Check if CSV file exists
    if not os.path.exists(csv_filename):
        print(f"Error: Could not find '{csv_filename}'. Please ensure it is in the same directory.")
        sys.exit(1)
    
    # 5. Generate MagicNumber
    if magic_number_start is not None:
        magic_number = int(magic_number_start)
        print(f"Starting MagicNumber (from config): {magic_number}")
    else:
        magic_number = random.randint(100000, 999999)
        print(f"Starting MagicNumber (random): {magic_number}")
    
    magic_number_start_value = magic_number
    
    # 6. Read the Template content
    try:
        with open(actual_template_filename, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template file: {e}")
        sys.exit(1)
    
    print(f"Successfully loaded template: {actual_template_filename}")
    print("-" * 50)
    
    # 7. Read CSV and Process Rows
    try:
        with open(csv_filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames is None:
                print("Error: CSV file is empty.")
                sys.exit(1)
            
            # Clean headers
            reader.fieldnames = [field.strip() for field in reader.fieldnames]
            
            count = 0
            for row in reader:
                try:
                    # Extract and strip whitespace from data
                    pair_name = row['Instrument'].strip()
                    year = row['Year'].strip()
                    price_high = row['Tip (High)'].strip()
                    price_low = row['Dip (Low)'].strip()
                    
                    # Calculate next year
                    next_year = calculate_next_year(year)
                    
                    # 8. Replace Placeholders in Content
                    new_content = template_content.replace('{PriceHighest}', price_high)
                    new_content = new_content.replace('{PriceLowest}', price_low)
                    new_content = new_content.replace('{TepVar}', tep_var)
                    new_content = new_content.replace('{MagicNumber}', str(magic_number))
                    new_content = new_content.replace('{timeFrame}', time_frame)
                    new_content = new_content.replace('{nextYear}', next_year)
                    
                    # 9. Construct Output Filename from Pattern
                    output_filename = template_pattern.replace('{pairName}', pair_name)
                    output_filename = output_filename.replace('{timeFrame}', time_frame)
                    output_filename = output_filename.replace('{nextYear}', next_year)
                    output_filename = output_filename.replace('{TepVar}', tep_var)
                    output_filename = output_filename.replace('{year}', year)
                    
                    # 10. Set CustomComment to the output filename (basename only)
                    new_content = new_content.replace('{CustomComment}', output_filename)
                    
                    # 11. Write New .set File to Output Directory
                    output_path = os.path.join(output_dir, output_filename)
                    
                    with open(output_path, 'w', encoding='utf-8') as out_f:
                        out_f.write(new_content)
                    
                    print(f"Generated: {output_dir}/{output_filename} (MagicNumber: {magic_number}, NextYear: {next_year})")
                    
                    # Increment MagicNumber for next file
                    magic_number += 1
                    count += 1
                    
                except KeyError as e:
                    print(f"Error: Missing column in CSV row: {e}")
                    continue
                except Exception as e:
                    print(f"Error processing row for {pair_name}: {e}")
                    continue
        
        print("-" * 50)
        print(f"Process complete. {count} files generated in './{output_dir}/' with TepVar={tep_var}.")
        print(f"MagicNumber range: {magic_number_start_value} to {magic_number - 1}")
        print("=" * 50)
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()