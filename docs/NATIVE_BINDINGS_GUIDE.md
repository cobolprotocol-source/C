# COBOL Protocol: Native Bindings Distribution Guide

## Overview

COBOL Protocol provides high-performance compression as native bindings for Python, Node.js, and Java. The core library is written in Rust with multi-layer compression (L1-L3).

## Installation

### Python (pip)

```bash
pip install cobol-protocol
```

Then use:
```python
from cobol_protocol import CobolCompressor

compressor = CobolCompressor()
compressed = compressor.compress(b"Hello World")
decompressed = compressor.decompress(compressed)
```

### Node.js (npm)

```bash
npm install cobol-protocol
```

Then use:
```javascript
const { CobolCompressor } = require('cobol-protocol');

const compressor = new CobolCompressor();
const compressed = compressor.compress(Buffer.from('Hello World'));
const decompressed = compressor.decompress(compressed);
```

### Java (Maven)

Add to `pom.xml`:
```xml
<dependency>