#!/usr/bin/env python3
"""Ingest official guidelines & resolutions into RAG document database.

Usage:
    python scripts/rag/ingest_documents.py [--dir data/raw/rag_docs] [--dry-run]
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.rag import Document, DocumentChunk
from app.models.scheme import Scheme


def parse_metadata_and_sections(file_path: Path) -> tuple[dict, list[tuple[str, str]]]:
    content = file_path.read_text(encoding="utf-8")
    meta = {}
    
    # Check for metadata block
    meta_match = re.search(r"=== DOCUMENT METADATA ===\n(.*?)\n=== END METADATA ===", content, re.DOTALL)
    if meta_match:
        meta_lines = meta_match.group(1).strip().splitlines()
        for line in meta_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        body = content[meta_match.end():].strip()
    else:
        body = content

    title = meta.get("title") or file_path.stem.replace("_", " ").title()
    source_name = meta.get("source_name") or "Government Portal"
    source_url = meta.get("source_url") or None
    document_type = meta.get("document_type") or "official_guidelines"
    language = meta.get("language") or "en"
    
    parsed_meta = {
        "title": title,
        "source_name": source_name,
        "source_url": source_url,
        "document_type": document_type,
        "language": language,
        "published_date": meta.get("published_date"),
        "effective_from": meta.get("effective_from"),
        "effective_until": meta.get("effective_until"),
    }

    # Split body into sections
    raw_sections = re.split(r"\n(?=SECTION:|\n#|\n##)", body)
    sections: list[tuple[str, str]] = []
    
    for idx, sec in enumerate(raw_sections, 1):
        sec_text = sec.strip()
        if not sec_text:
            continue
        sec_title = f"Section {idx}"
        if sec_text.startswith("SECTION:"):
            first_line, _, rest = sec_text.partition("\n")
            sec_title = first_line.replace("SECTION:", "").strip()
            sec_body = rest.strip()
        else:
            sec_body = sec_text

        if sec_body:
            sections.append((sec_title, sec_body))

    if not sections and body:
        sections.append(("Main Content", body))

    return parsed_meta, sections


def ingest_documents(docs_dir: Path, dry_run: bool = False) -> None:
    if not docs_dir.exists():
        print(f"Directory not found: {docs_dir}")
        return

    doc_files = sorted(list(docs_dir.glob("*.txt")) + list(docs_dir.glob("*.md")))
    if not doc_files:
        print(f"No document files found in {docs_dir}")
        return

    print(f"Found {len(doc_files)} document(s) for ingestion.")

    with Session(engine) as db:
        # Build map of existing scheme names for linking
        all_schemes = db.exec(select(Scheme)).all()
        scheme_map = {s.name.lower(): s.id for s in all_schemes}

        imported_docs = 0
        imported_chunks = 0

        for file_path in doc_files:
            meta, sections = parse_metadata_and_sections(file_path)
            content_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()

            existing_doc = db.exec(
                select(Document).where(Document.content_hash == content_hash)
            ).first()

            if existing_doc:
                doc = existing_doc
                print(f"Updating existing document: '{doc.title}' ({doc.id})")
            else:
                eff_from = (
                    datetime.strptime(meta["effective_from"], "%Y-%m-%d").date()
                    if meta.get("effective_from")
                    else None
                )
                doc = Document(
                    title=meta["title"],
                    source_name=meta["source_name"],
                    source_url=meta.get("source_url"),
                    document_type=meta["document_type"],
                    language=meta["language"],
                    file_path=str(file_path),
                    effective_from=eff_from,
                    content_hash=content_hash,
                    active=True,
                    last_verified_at=datetime.utcnow(),
                )
                db.add(doc)
                db.flush()
                imported_docs += 1

            # Match scheme if doc title mentions a scheme name
            matched_scheme_id = None
            for s_name, s_id in scheme_map.items():
                if any(k in doc.title.lower() for k in s_name.split() if len(k) > 3):
                    matched_scheme_id = s_id
                    break

            # Ingest chunks
            for chunk_idx, (sec_title, sec_content) in enumerate(sections, 1):
                existing_chunk = db.exec(
                    select(DocumentChunk).where(
                        DocumentChunk.document_id == doc.id,
                        DocumentChunk.chunk_index == chunk_idx,
                    )
                ).first()

                if existing_chunk:
                    existing_chunk.content = sec_content
                    existing_chunk.section_title = sec_title
                    existing_chunk.scheme_id = matched_scheme_id
                    db.add(existing_chunk)
                else:
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        scheme_id=matched_scheme_id,
                        chunk_index=chunk_idx,
                        content=sec_content,
                        page_number=chunk_idx,
                        section_title=sec_title,
                    )
                    db.add(chunk)
                    imported_chunks += 1

        if not dry_run:
            db.commit()
            print(f"Successfully ingested {imported_docs} documents and {imported_chunks} chunks.")
        else:
            db.rollback()
            print(f"Dry-run: validated {imported_docs} documents and {imported_chunks} chunks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest RAG documents into database")
    parser.add_argument(
        "--dir", default="data/raw/rag_docs", help="Directory containing raw document text files"
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    args = parser.parse_args()
    ingest_documents(Path(args.dir), dry_run=args.dry_run)
