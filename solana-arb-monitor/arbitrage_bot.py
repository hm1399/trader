import aiohttp
import asyncio
import csv
import os
import json
from datetime import datetime
import signal
import sys
from typing import Dict, List, Optional

class QuickTokenChecker:
    def __init__(self, token_file):
        self.jupiter_base_url = "https://quote-api.jup.ag/v6/quote"
        self.raydium_base_url = "https://api.raydium.io/v2/main/price"
        self.sol_address = 'So11111111111111111111111111111111111111112'
        
        # Load tokens from JSON file
        with open(token_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'tokens' in data:
                self.token_addresses = {
                    symbol: info['address'] 
                    for symbol, info in data['tokens'].items()
                }
            else:
                self.token_addresses = data
        
        print(f"Loaded {len(self.token_addresses)} tokens to check")

    async def get_with_timeout(self, session, url, timeout=5, max_retries=3, **kwargs):
        """Make a GET request with timeout and retry logic"""
        for attempt in range(max_retries):
            try:
                async with asyncio.timeout(timeout):
                    async with session.get(url, **kwargs) as response:
                        if response.status == 429:  # Rate limit hit
                            retry_after = int(response.headers.get('Retry-After', 5))
                            await asyncio.sleep(retry_after)
                            continue
                            
                        status = response.status
                        try:
                            data = await response.json()
                            return status, data
                        except Exception as e:
                            text = await response.text()
                            return status, None
                            
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
                
        return None, None
    
    async def get_pool_address(self, session, token_address):
        """Get pool address from DexScreener"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    # Find Raydium pair
                    for pair in pairs:
                        if pair.get('dexId') == 'raydium':
                            return {
                                'pair_address': pair.get('pairAddress'),
                                'price': float(pair.get('priceUsd', 0))
                            }
            return None
        except Exception:
            return None

    async def check_jupiter(self, session, symbol, address):
        # First get SOL/USDC price
        sol_price_params = {
            'inputMint': self.sol_address,
            'outputMint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'amount': '1000000000',
            'slippageBps': 50
        }
        
        sol_status, sol_data = await self.get_with_timeout(session, self.jupiter_base_url, params=sol_price_params)
        if not sol_status == 200 or not sol_data or 'outAmount' not in sol_data:
            return False, None
            
        sol_price_usdc = float(sol_data['outAmount']) / 1e6  # Convert to decimal USDC
        
        # Get token/SOL price
        params = {
            'inputMint': address,
            'outputMint': self.sol_address,
            'amount': '1000000000',
            'slippageBps': 50
        }
        
        status, data = await self.get_with_timeout(session, self.jupiter_base_url, params=params)
        
        if status == 200 and data and 'outAmount' in data:
            sol_value = float(data['outAmount']) / float(params['amount'])
            usdc_price = (sol_value * sol_price_usdc) / 1000  # Divide by 1000
            
            return True, {
                'price': usdc_price
            }
        return False, None

    async def check_raydium(self, session, symbol, address):
        """Check token price on Raydium"""
        pool_data = await self.get_pool_address(session, address)
        if not pool_data:
            return False, None
            
        return True, {
            'price': pool_data['price']
        }

class ArbitrageMonitor(QuickTokenChecker):
    def __init__(self, token_file: str, config: Dict):
        super().__init__(token_file)
        self.config = config
        self.running = False
        self.last_check_times: Dict[str, datetime] = {}
        self.error_counts: Dict[str, int] = {}
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown on signals"""
        print("\nShutdown signal received. Cleaning up...")
        self.running = False

    async def monitor_token(self, session: aiohttp.ClientSession, symbol: str, address: str) -> Optional[dict]:
        """Monitor a single token pair with error handling and rate limiting"""
        try:
            # Check if we need to wait due to rate limiting
            last_check = self.last_check_times.get(symbol)
            if last_check:
                time_since_last = (datetime.now() - last_check).total_seconds()
                if time_since_last < self.config['min_check_interval']:
                    await asyncio.sleep(self.config['min_check_interval'] - time_since_last)

            # Update last check time
            self.last_check_times[symbol] = datetime.now()

            # Check prices
            raydium_available, raydium_data = await self.check_raydium(session, symbol, address)
            if raydium_available:
                await asyncio.sleep(0.1)  # Small delay between checks
                jupiter_available, jupiter_data = await self.check_jupiter(session, symbol, address)
                
                if jupiter_available and raydium_data and jupiter_data:
                    ray_price = float(raydium_data['price'])
                    jup_price = float(jupiter_data['price'])
                    
                    diff_percent = abs(ray_price - jup_price) / min(ray_price, jup_price) * 100
        
                    if diff_percent > self.config['min_price_difference']:
                        # Determine buy/sell venues based on prices
                        buy_price = min(ray_price, jup_price)
                        sell_price = max(ray_price, jup_price)
                        buy_on = 'Raydium' if buy_price == ray_price else 'Jupiter'
                        sell_on = 'Jupiter' if sell_price == jup_price else 'Raydium'
                        
                        opportunity = {
                            'symbol': symbol,
                            'address': address,
                            'buy_on': buy_on,
                            'sell_on': sell_on,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'difference_percent': diff_percent,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        return opportunity
        
                return None

        except Exception as e:
            self.error_counts[symbol] = self.error_counts.get(symbol, 0) + 1
            if self.error_counts[symbol] > self.config['max_errors']:
                print(f"Too many errors for {symbol}, considering removal from monitoring")
            return None

    async def run_monitoring_loop(self):
        """Main monitoring loop with proper error handling and rate limiting"""
        self.running = True
        print(f"Starting monitoring loop at {datetime.now()}")
        
        while self.running:
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    while self.running:
                        start_time = datetime.now()
                        opportunities = []

                        for symbol, address in self.token_addresses.items():
                            if symbol != 'SOL':
                                try:
                                    result = await self.monitor_token(session, symbol, address)
                                    if isinstance(result, dict):
                                        opportunities.append(result)
                                except Exception as e:
                                    continue

                        if opportunities:
                            self.save_opportunities(opportunities)
                            
                            for opp in opportunities:
                                print(f"\n🔥 Opportunity found for {opp['symbol']}:")
                                print(f"Buy on {opp['buy_on']} at ${opp['buy_price']:.6f}")
                                print(f"Sell on {opp['sell_on']} at ${opp['sell_price']:.6f}")
                                print(f"Difference: {opp['difference_percent']:.2f}%")

                        elapsed = (datetime.now() - start_time).total_seconds()
                        if elapsed < self.config['check_interval']:
                            await asyncio.sleep(self.config['check_interval'] - elapsed)

            except Exception as e:
                print("Restarting monitoring loop in 10 seconds...")
                await asyncio.sleep(10)

    def save_opportunities(self, opportunities):
        """Save opportunities to CSV file"""
        csv_filename = 'arbitrage_opportunities.csv'
        file_exists = os.path.exists(csv_filename)
        
        with open(csv_filename, 'a', newline='') as f:
            headers = [
                'timestamp',
                'symbol',
                'address',
                'buy_on',
                'sell_on',
                'buy_price',
                'sell_price',
                'difference_percent'
            ]
            
            writer = csv.DictWriter(f, fieldnames=headers)
            
            if not file_exists:
                writer.writeheader()
            
            for opp in opportunities:
                row = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'symbol': opp['symbol'],
                    'address': opp['address'],
                    'buy_on': opp['buy_on'],
                    'sell_on': opp['sell_on'],
                    'buy_price': f"{opp['buy_price']:.8f}",
                    'sell_price': f"{opp['sell_price']:.8f}",
                    'difference_percent': f"{opp['difference_percent']:.2f}"
                }
                writer.writerow(row)
        
        print(f"\nLogged {len(opportunities)} opportunities to {csv_filename}")

async def main():
    # Configuration
    config = {
        'check_interval': 30,  # Seconds between full check cycles
        'min_check_interval': 0,  # Minimum seconds between checks for same token
        'min_price_difference': 0.1,  # Minimum price difference percentage
        'max_errors': 5,  # Maximum errors before warning
        'token_file': 'sols_pairs.json'
    }

    monitor = ArbitrageMonitor(config['token_file'], config)
    
    try:
        await monitor.run_monitoring_loop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        print("\nShutting down...")

if __name__ == "__main__":
    print("Starting the p05h SOL arbitrage monitor...")
    asyncio.run(main())