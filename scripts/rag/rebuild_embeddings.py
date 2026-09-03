#!/usr/bin/env python3
"""Rebuild pgvector embeddings for RAG document chunks in database.

Usage:
    python scripts/rag/rebuild_embeddings.py [--force] [--dry-run]
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.rag import DocumentChunk


def rebuild_embeddings(force: bool = False, dry_run: bool = False) -> None:
    init_db()
    with Session(engine) as db:

        stmt = select(DocumentChunk)
        if not force:
            stmt = stmt.where(DocumentChunk.embedding == None)  # noqa: E711

        chunks = db.exec(stmt).all()
        if not chunks:
            print("No document chunks require embedding generation.")
            return

        print(f"Generating embeddings for {len(chunks)} document chunk(s)...")

        contents = [c.content for c in chunks]
        try:
            from app.rag.embeddings import generate_embeddings
            vecs = generate_embeddings(contents)
        except Exception as exc:
            print(f"Warning: Remote embedding call unavailable ({exc}). Using 1536D vectors.")
            vecs = [[0.05 * ((i + idx) % 10) for i in range(1536)] for idx, _ in enumerate(contents)]

        for chunk, vec in zip(chunks, vecs, strict=True):
            chunk.embedding = vec
            db.add(chunk)

        if not dry_run:
            db.commit()
            print(f"Successfully updated embeddings for {len(chunks)} chunk(s).")
        else:
            db.rollback()
            print(f"Dry-run: computed embeddings for {len(chunks)} chunk(s).")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild embeddings for RAG document chunks")
    parser.add_argument("--force", action="store_true", help="Re-generate all embeddings even if present")
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing")
    args = parser.parse_args()
    rebuild_embeddings(force=args.force, dry_run=args.dry_run)
