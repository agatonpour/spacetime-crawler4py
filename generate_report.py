#!/usr/bin/env python3
"""
Generate the analytics report after crawling is complete.
Run this after your crawler finishes.
"""

from analytics import Analytics

def main():
    # Load analytics
    analytics = Analytics()
    
    # Generate and print report
    report = analytics.generate_report()
    print(report)
    
    # Also save to file
    with open("REPORT.txt", "w") as f:
        f.write(report)
    
    print("\nReport saved to REPORT.txt")

if __name__ == "__main__":
    main()

