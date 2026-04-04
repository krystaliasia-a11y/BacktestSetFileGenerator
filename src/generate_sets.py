import csv
import os
import sys
import random

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)

# Repository root (parent of src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(relative_or_abs):
    """Resolve a path from config: absolute paths unchanged; others relative to PROJECT_ROOT."""
    if os.path.isabs(relative_or_abs):
        return relative_or_abs
    return os.path.normpath(os.path.join(PROJECT_ROOT, relative_or_abs))


def load_config(config_filename=None):
    """Load configuration from YAML file (default: config/config.yaml under repo root)."""
    path = config_filename or os.path.join(PROJECT_ROOT, 'config', 'config.yaml')
    if not os.path.exists(path):
        print(f"Error: Could not find '{path}'.")
        print("\nExample config.yaml:")
        print(
            """\
csv_file: config/pair_data.csv
template_file: config/template.set
template_pattern: "SRM_v6.0_AlgoX_REAL-{pairName}-{timeFrame}-{nextYear}0101-{nextYear}1231-{Spread}-TEP{TepVar}_TBBB{year}.set"
spread: "15"
open_order_buffer_pct: 5
equity_assumption: "10000.00000000"
real_equity: "10000.00000000"
tep_var: "0"
take_profit_ratio: "0.70000000"
pullback_ratio: "0.00000000"
drop_ratio: "0.10000000"
brounce_ratio: "0.05000000"
timeFrame: H1
magic_number_start: null
output_dir: output
"""
        )
        sys.exit(1)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print("Error: Config file must contain a YAML mapping (key/value pairs) at the root.")
        sys.exit(1)

    return config


def calculate_next_year(year_str):
    """Calculate next year from current year string"""
    try:
        current_year = int(year_str)
        next_year = current_year + 1
        return str(next_year)
    except ValueError:
        print(f"Warning: Invalid year format '{year_str}', using same year")
        return year_str


def format_price_level(value):
    """Format computed price for .set files (8 decimal places)."""
    return f'{float(value):.8f}'


def open_order_thresholds(tip_high, dip_low, buffer_pct):
    """
    buffer_pct is percent of (Tip - Dip) trimmed from each end of the range.
    LargerThan = dip + margin; SmallerThan = tip - margin (same for buy and sell per spec).
    """
    tip = float(tip_high)
    dip = float(dip_low)
    span = tip - dip
    margin = span * float(buffer_pct) / 100.0
    larger = dip + margin
    smaller = tip - margin
    lv = format_price_level(larger)
    sv = format_price_level(smaller)
    return lv, sv


def main():
    config = load_config()

    csv_filename = resolve_path(config.get('csv_file', 'config/pair_data.csv'))
    template_path = resolve_path(config.get('template_file', 'config/template.set'))
    template_pattern = config.get(
        'template_pattern',
        'SRM_v6.0_AlgoX_REAL-{pairName}-{timeFrame}-{nextYear}0101-{nextYear}1231-{Spread}-TEP{TepVar}_TBBB{year}.set',
    )
    equity_assumption = str(config.get('equity_assumption', '10000.00000000'))
    real_equity = str(config.get('real_equity', '10000.00000000'))
    tep_var = str(config.get('tep_var', '0'))
    take_profit_ratio = str(config.get('take_profit_ratio', '0.70000000'))
    pullback_ratio = str(config.get('pullback_ratio', '0.00000000'))
    drop_ratio = str(config.get('drop_ratio', '0.10000000'))
    brounce_ratio = str(config.get('brounce_ratio', '0.05000000'))
    spread = str(config.get('spread', '0'))
    open_order_buffer_pct = config.get('open_order_buffer_pct', 0)
    time_frame = str(config.get('timeFrame', 'H1'))
    magic_number_start = config.get('magic_number_start', None)
    output_dir = resolve_path(config.get('output_dir', 'output'))

    print("=" * 50)
    print("Configuration Loaded:")
    print(f"  CSV File: {csv_filename}")
    print(f"  Template File: {template_path}")
    print(f"  Template Pattern: {template_pattern}")
    print(f"  EquityAssumption: {equity_assumption}")
    print(f"  RealEquity: {real_equity}")
    print(f"  TepVar: {tep_var}")
    print(f"  TakeProfitRatio: {take_profit_ratio}")
    print(f"  PullbackRatio: {pullback_ratio}")
    print(f"  DropRatio: {drop_ratio}")
    print(f"  BrounceRatio: {brounce_ratio}")
    print(f"  Spread: {spread}")
    print(f"  Open order buffer %: {open_order_buffer_pct}")
    print(f"  TimeFrame: {time_frame}")
    print(f"  Output Directory: {output_dir}")
    print("=" * 50)

    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory ready: {output_dir}")
    except Exception as e:
        print(f"Error creating output directory: {e}")
        sys.exit(1)

    if not os.path.isfile(template_path):
        print(f"Error: Template file not found: {template_path}")
        sys.exit(1)

    print(f"Using template file: {template_path}")

    if not os.path.exists(csv_filename):
        print(f"Error: Could not find CSV file: {csv_filename}")
        sys.exit(1)

    if magic_number_start is not None:
        magic_number = int(magic_number_start)
        print(f"Starting MagicNumber (from config): {magic_number}")
    else:
        magic_number = random.randint(100000, 999999)
        print(f"Starting MagicNumber (random): {magic_number}")

    magic_number_start_value = magic_number

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template file: {e}")
        sys.exit(1)

    print(f"Successfully loaded template: {template_path}")
    print("-" * 50)

    try:
        with open(csv_filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                print("Error: CSV file is empty.")
                sys.exit(1)

            reader.fieldnames = [field.strip() for field in reader.fieldnames]

            count = 0
            for row in reader:
                pair_name = None
                try:
                    pair_name = row['Instrument'].strip()
                    year = row['Year'].strip()
                    price_high = row['Tip (High)'].strip()
                    price_low = row['Dip (Low)'].strip()

                    next_year = calculate_next_year(year)

                    ob_larger, ob_smaller = open_order_thresholds(
                        price_high, price_low, open_order_buffer_pct
                    )

                    new_content = template_content.replace('{PriceHighest}', price_high)
                    new_content = new_content.replace('{PriceLowest}', price_low)
                    new_content = new_content.replace('{OpenBuyLargerThan}', ob_larger)
                    new_content = new_content.replace('{OpenBuySmallerThan}', ob_smaller)
                    new_content = new_content.replace('{OpenSellLargerThan}', ob_larger)
                    new_content = new_content.replace('{OpenSellSmallerThan}', ob_smaller)
                    new_content = new_content.replace('{Spread}', spread)
                    new_content = new_content.replace('{EquityAssumption}', equity_assumption)
                    new_content = new_content.replace('{RealEquity}', real_equity)
                    new_content = new_content.replace('{TepVar}', tep_var)
                    new_content = new_content.replace('{TakeProfitRatio}', take_profit_ratio)
                    new_content = new_content.replace('{PullbackRatio}', pullback_ratio)
                    new_content = new_content.replace('{DropRatio}', drop_ratio)
                    new_content = new_content.replace('{BrounceRatio}', brounce_ratio)
                    new_content = new_content.replace('{MagicNumber}', str(magic_number))
                    new_content = new_content.replace('{timeFrame}', time_frame)
                    new_content = new_content.replace('{nextYear}', next_year)

                    output_filename = template_pattern.replace('{pairName}', pair_name)
                    output_filename = output_filename.replace('{timeFrame}', time_frame)
                    output_filename = output_filename.replace('{nextYear}', next_year)
                    output_filename = output_filename.replace('{Spread}', spread)
                    output_filename = output_filename.replace('{TepVar}', tep_var)
                    output_filename = output_filename.replace('{year}', year)

                    new_content = new_content.replace('{CustomComment}', output_filename)

                    output_path = os.path.join(output_dir, output_filename)

                    with open(output_path, 'w', encoding='utf-8') as out_f:
                        out_f.write(new_content)

                    print(
                        f"Generated: {output_path} (MagicNumber: {magic_number}, NextYear: {next_year})"
                    )

                    magic_number += 1
                    count += 1

                except KeyError as e:
                    print(f"Error: Missing column in CSV row: {e}")
                    continue
                except Exception as e:
                    label = pair_name or "(unknown pair)"
                    print(f"Error processing row for {label}: {e}")
                    continue

        print("-" * 50)
        print(f"Process complete. {count} files generated in '{output_dir}' with TepVar={tep_var}.")
        print(f"MagicNumber range: {magic_number_start_value} to {magic_number - 1}")
        print("=" * 50)

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
