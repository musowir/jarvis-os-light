# ==============================================================================
# SYSTEM INSTANCE CODE BASE : JARVIS CORE FRAMEWORK
# MODULE          : core.markdown_cleaner
# DESCRIPTION     : Strips markdown syntax structural elements, text wrappers, and formatting 
#                   markers to output flat, conversational prose structures.
# COORDINATES     : Layer-2 Core Background Engines
# SUBSYSTEM       : Text Processing & Token Optimization Pipeline
# ==============================================================================

import re

def strip_markdown(text: str) -> str:
    """
    Transforms structural markdown data into clean, uninterrupted prose text blocks.
    Removes syntax signatures (headers, links, code blocks) to optimize context window limits.
    """
    if not text:
        return ""

    # 1. Strip out multi-line or inline code/pre-formatted block boundaries
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 2. Strip images syntax: ![alt text](url) -> preservation of alt text description only
    text = re.sub(r'!\[([^\]]*)]\([^)]*\)', r'\1', text)

    # 3. Strip hyperlinked text anchors: [Link Text](http://...) -> Link Text
    text = re.sub(r'\[([^\]]+)]\([^)]*\)', r'\1', text)

    # 4. Strip heading hashes while keeping text: ### Heading Name -> Heading Name
    text = re.sub(r'(?m)^#{1,6}\s+(.+)$', r'\1', text)

    # 5. Clean out bold and italic character wrappers
    text = re.sub(r'\*\*|__|[\*_]', '', text)

    # 6. Remove bullet/ordered list symbols at the start of lines
    text = re.sub(r'(?m)^[-\*\+]\s+', '', text)
    text = re.sub(r'(?m)^\d+\.\s+', '', text)

    # 7. Strip blockquote symbols
    text = re.sub(r'(?m)^>\s+', '', text)

    # 8. Unify broken white spaces, structural indents, and trailing breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
