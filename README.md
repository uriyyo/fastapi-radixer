# FastAPI Radixer

A high-performance HTTP router for FastAPI applications using radix tree-based routing to achieve faster route lookup and matching compared to FastAPI's default routing system.

## Overview

FastAPI Radixer is a Python library that provides a drop-in replacement for FastAPI's default router with significant performance improvements. It uses a radix tree (compressed trie) data structure to efficiently store and lookup routes, making it ideal for applications with large numbers of endpoints or performance-critical routing requirements.

## Key Features

- **High-Performance Routing**: Radix tree-based implementation for O(k) route lookup complexity where k is the length of the path
- **Drop-in Replacement**: Seamlessly integrates with existing FastAPI applications without breaking changes
- **Rust-Powered**: Core routing logic implemented in Rust using PyO3 for maximum performance
- **Comprehensive Benchmarking**: Built-in benchmark suite with real-world API patterns (Spotify API endpoints)
- **Full FastAPI Compatibility**: Supports all FastAPI routing features including path parameters, dependency injection, and middleware

## Project Goals

### Primary Objectives

1. **Performance Optimization**: Dramatically improve route lookup performance in FastAPI applications, especially those with many routes
2. **Scalability**: Enable FastAPI applications to handle thousands of routes without performance degradation
3. **Zero Breaking Changes**: Provide a seamless upgrade path that doesn't require application code changes
4. **Production Ready**: Deliver a stable, well-tested library suitable for production workloads

### Technical Goals

- Achieve sub-microsecond route lookup times for typical web application routing patterns
- Maintain full compatibility with FastAPI's routing API and features
- Provide comprehensive benchmarking tools to validate performance improvements
- Support all HTTP methods and complex path patterns including wildcards and parameters

## Installation

```bash
pip install fastapi-radixer
```

## Quick Start

### Initialize Existing FastAPI App

```python
from fastapi import FastAPI
from fastapi_radixer import init_app

app = FastAPI()

# Add your routes as normal
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    return {"user_id": user_id}

# Initialize Radixer (replaces default router)
init_app(app)
```

## Benchmarks

Run the included benchmark suite to see performance improvements:

```bash
python -m benchmarks.runner
```

The benchmark suite includes 70+ endpoints based on the Spotify Web API, covering:
- RESTful CRUD operations
- Complex path parameters
- Nested resource endpoints
- Various HTTP methods

## Performance

FastAPI Radixer provides significant performance improvements over FastAPI's default routing based on comprehensive benchmarks with 70+ endpoints:

### Benchmark Results

**Simple Routes (/, /health)**:
- **2.98x faster** median response time (11.88ms vs 36.04ms)
- **2.98x faster** mean response time (12.44ms vs 37.13ms)

**API Endpoints with Path Parameters**:
- `/artists/{id}`: **1.24x faster** (14.52ms vs 18.02ms mean)
- `/audio-features/{id}`: **1.25x faster** (13.91ms vs 17.38ms mean)
- `/episodes/{id}`: **2.35x faster** (14.04ms vs 33.00ms mean)

**Complex Nested Routes**:
- `/browse/categories`: **2.55x faster** (12.36ms vs 31.48ms mean)
- `/browse/featured-playlists`: **2.50x faster** (12.28ms vs 30.67ms mean)
- `/me/episodes`: **2.82x faster** (12.50ms vs 35.23ms mean)

**Player Control Endpoints**:
- `/me/player/currently-playing`: **2.23x faster** (11.85ms vs 26.38ms mean)
- `/me/player/devices`: **2.16x faster** (11.93ms vs 25.77ms mean)
- `/me/player/pause`: **2.30x faster** (11.81ms vs 27.14ms mean)

### Key Performance Characteristics

- **Consistent Performance**: Radixer maintains ~11-15ms response times across all endpoint types
- **Linear Degradation**: FastAPI's default router shows significant slowdown with complex paths (up to 35ms)
- **Memory Efficiency**: Compressed radix tree structure uses less memory than linear route matching
- **Scalability**: Performance remains consistent even with thousands of routes

### Best Performance Gains

Routes with the highest improvement factors:
- **3x faster**: Simple static routes and health checks
- **2.8x faster**: Complex nested user endpoints 
- **2.5x faster**: Browse and discovery endpoints
- **2.3x faster**: Real-time player control endpoints

## License

This project is licensed under the MIT License - see the LICENSE file for details.
