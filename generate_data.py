#!/usr/bin/env python3
"""
HBase Web Table Data Generator
This script runs inside the HBase RegionServer container to create and populate
the webtable with sample web page data using the specified schema and salting.
"""

import happybase
import random
import hashlib
import time
from datetime import datetime, timedelta
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuration
NUM_PAGES = 25  # Generate at least 20 pages (a few extra for good measure)
DOMAINS = ['help.com', 'please.org', 'example.net', 'support.io', 'docs.edu']
CONTENT_SIZES = ['small', 'medium', 'large']
SALT_PREFIXES = ['00', '10', '20', '30', '40', '50', '60', '70', '80', '90', 'a0', 'b0', 'c0', 'd0', 'e0', 'f0']
MAX_AGE_DAYS = 180  # Maximum age of content in days

# HBase connection details
HBASE_HOST = 'localhost'
HBASE_PORT = 9090  # Default HBase Thrift port

class WebTableGenerator:
    """Generates sample web data in HBase webtable"""
    
    def __init__(self):
        self.connection = None
        self.table = None
        self.all_pages = {}  # Dictionary to track created pages {row_key: url}
    
    def connect_to_hbase(self):
        """Establish connection to HBase and create table if it doesn't exist"""
        try:
            logger.info(f"Connecting to HBase at {HBASE_HOST}:{HBASE_PORT}")
            self.connection = happybase.Connection(HBASE_HOST, HBASE_PORT)
            
            # Check if table exists, create if it doesn't
            if b'webtable' not in self.connection.tables():
                logger.info("Creating webtable...")
                self.create_table()
            else:
                logger.info("webtable already exists, using existing table")
            
            self.table = self.connection.table('webtable')
            logger.info("Connection established successfully")
            return True
        except Exception as e:
            # Handle the case where the exception message is bytes
            error_msg = e
            if hasattr(e, '__str__') and isinstance(e.__str__(), bytes):
                try:
                    error_msg = e.__str__().decode('utf-8')
                except:
                    error_msg = f"<Binary exception: {repr(e)}>"
            logger.error(f"Failed to connect to HBase: {error_msg}")
            return False
    
    def create_table(self):
        """Create the webtable with specified column families"""
        families = {
            'content': {'versions': 3, 'time_to_live': 7776000},  # 90 days in seconds
            'metadata': {'versions': 1},                          # No TTL
            'outlinks': {'versions': 2, 'time_to_live': 15552000},# 180 days
            'inlinks': {'versions': 2, 'time_to_live': 15552000}  # 180 days
        }
        self.connection.create_table('webtable', families)
    
    def get_salted_rowkey(self, domain, path):
        """Generate a salted row key using one of the specified salt prefixes"""
        # Create a hash based on domain to consistently map same domains to same salts
        domain_hash = int(hashlib.md5(domain.encode()).hexdigest(), 16)
        
        # Select salt from predefined list using the hash (consistent mapping)
        salt = SALT_PREFIXES[domain_hash % len(SALT_PREFIXES)]
        
        # Reverse domain parts and join with dots
        reversed_domain = '.'.join(reversed(domain.split('.')))
        
        # Construct final row key: salt:reversed_domain/path
        row_key = f"{salt}:{reversed_domain}{path}"
        return row_key, f"http://{domain}{path}"
    
    def generate_content(self, size):
        """Generate HTML content of specified size"""
        paragraphs = [
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl nec ultricies lacinia.",
            "Phasellus non metus dapibus, sagittis ante non, mollis velit. Fusce aliquam eros vitae purus consequat, in scelerisque orci pellentesque.",
            "Donec eget ipsum eget dolor rutrum malesuada. Suspendisse potenti. Etiam bibendum magna vitae justo feugiat, nec maximus elit laoreet.",
            "Integer lacinia ante quis eros elementum, sit amet mollis libero auctor. Morbi a massa vel ex scelerisque commodo.",
            "Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Cras nec risus vel sem efficitur sagittis."
        ]
        
        if size == 'small':
            content_paragraphs = random.sample(paragraphs, 1)
        elif size == 'medium':
            content_paragraphs = random.sample(paragraphs, 3)
        else:  # large
            content_paragraphs = paragraphs
        
        title = f"Sample {size.capitalize()} Page"
        content = "\n".join(content_paragraphs)
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>{title}</h1>
    {''.join([f'<p>{p}</p>' for p in content_paragraphs])}
</body>
</html>"""
        
        return html
    
    def generate_timestamp(self):
        """Generate a random timestamp within the last MAX_AGE_DAYS days"""
        age_days = random.randint(0, MAX_AGE_DAYS)
        timestamp = datetime.now() - timedelta(days=age_days)
        return timestamp.isoformat()
    
    def create_sample_pages(self):
        """First pass: Generate sample pages with basic data"""
        logger.info(f"Generating {NUM_PAGES} sample web pages...")
        
        for i in range(NUM_PAGES):
            # Select random attributes
            domain = random.choice(DOMAINS)
            path = f"/{random.choice(['home', 'about', 'contact', 'products', 'services', 'blog', 'faq', 'support'])}"
            path += f"/{random.randint(100, 999)}"
            
            size = random.choice(CONTENT_SIZES)
            modified_date = self.generate_timestamp()
            
            # Generate salted row key
            row_key, url = self.get_salted_rowkey(domain, path)
            
            # Store in tracking dictionary for linking later
            self.all_pages[row_key] = url
            
            # Insert page data with empty outlinks/inlinks (to be populated later)
            self.table.put(row_key, {
                # Content family
                'content:html': self.generate_content(size),
                
                # Metadata family
                'metadata:title': f"{domain.split('.')[0].capitalize()} {path.split('/')[-1]} Page",
                'metadata:size': size,
                'metadata:domain': domain,
                'metadata:path': path,
                'metadata:modified': modified_date,
                
                # Empty outlinks/inlinks (populated in second pass)
                'outlinks:list': '',
                'inlinks:list': ''
            })
            
            logger.info(f"Created page {i+1}/{NUM_PAGES}: {url} (row_key: {row_key})")
        
        logger.info(f"Successfully generated {NUM_PAGES} basic pages")
    
    def create_link_structure(self):
        """Second pass: Create interconnected link structure"""
        logger.info("Creating interconnected link structure...")
        
        page_keys = list(self.all_pages.keys())
        
        for row_key in page_keys:
            # Select 2-5 random pages to link to (outlinks)
            num_outlinks = random.randint(2, 5)
            possible_outlinks = [k for k in page_keys if k != row_key]
            outlink_keys = random.sample(
                possible_outlinks, 
                min(num_outlinks, len(possible_outlinks))
            )
            
            # Create outlinks list
            outlinks = [self.all_pages[k] for k in outlink_keys]
            outlinks_str = ','.join(outlinks)
            
            # Update outlinks for this page
            self.table.put(row_key, {
                'outlinks:list': outlinks_str
            })
            
            # Update inlinks for each linked page
            for outlink_key in outlink_keys:
                # Get current inlinks
                row = self.table.row(outlink_key, columns=[b'inlinks:list'])
                current_inlinks = row.get(b'inlinks:list', b'').decode() if row else ''
                
                # Add this page URL as an inlink
                new_inlinks = current_inlinks
                if new_inlinks:
                    new_inlinks += ','
                new_inlinks += self.all_pages[row_key]
                
                # Update inlinks
                self.table.put(outlink_key, {
                    'inlinks:list': new_inlinks
                })
        
        logger.info("Successfully created interconnected link structure")
    
    def run(self):
        """Run the complete data generation process"""
        if not self.connect_to_hbase():
            return False
        
        try:
            # First pass: Create basic pages
            self.create_sample_pages()
            
            # Second pass: Create interconnected links
            self.create_link_structure()
            
            logger.info("Data generation completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error generating data: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()
                logger.info("Connection closed")

if __name__ == "__main__":
    generator = WebTableGenerator()
    success = generator.run()
    sys.exit(0 if success else 1) 