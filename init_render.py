#!/usr/bin/env python
"""
Render Deployment Initialization Script

Safely initializes the database for Render Free deployments where shell
access is not available.

- Creates tables only if they don't exist
- Seeds data only if database is empty
- Safe to run repeatedly without duplicating data
- Does NOT drop tables or delete existing data
"""

import os
import sys


def init_render_database():
    print("=" * 60)
    print("RENDER DATABASE INITIALIZATION")
    print("=" * 60)
    print()

    from app import app, db
    from models import User
    from app import seed_database

    with app.app_context():
        print("Step 1: Creating database tables...")
        try:
            db.create_all()
            print("  ✓ Database tables created/verified")
        except Exception as e:
            print(f"  ✗ Error creating tables: {e}")
            return False

        print()
        print("Step 2: Checking for existing data...")

        try:
            user_count = User.query.count()
            print(f"  Found {user_count} users in database")

            if user_count > 0:
                print()
                print("  ✓ Database already contains data")
                print("  Skipping seed data to avoid duplicates")
                print()
                print("=" * 60)
                print("INITIALIZATION COMPLETE (existing data preserved)")
                print("=" * 60)
                return True

            print("  Database is empty - proceeding with seed data")
        except Exception as e:
            print(f"  ✗ Error checking existing data: {e}")
            return False

        print()
        print("Step 3: Seeding development data...")

        try:
            seed_database()
            print("  ✓ Development data seeded")
        except Exception as e:
            print(f"  ✗ Error seeding data: {e}")
            return False

        print()
        print("=" * 60)
        print("INITIALIZATION COMPLETE")
        print("=" * 60)
        return True


if __name__ == '__main__':
    init_render_database()
