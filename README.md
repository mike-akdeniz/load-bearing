# Load-Bearing

*Which Software Principles Hold, and Where They Stop*

"Dependencies must be acyclic" is nearly a mathematical fact.

"Every repository gets an interface" is a local convention of one ecosystem.

Both arrive in the same tone of voice, with equal confidence, so the local convention gets applied everywhere as if it were a mathematical fact.

This book is a field guide for telling the difference.
Its central question is the one a builder asks before knocking out a wall: **is this load-bearing?**
Some walls carry the structure.
Some are partitions someone painted to look structural.
Removing the first brings the roof down; removing the second is redecorating.

**→ [Start reading: Chapter 01, Is This Load-Bearing?](01_load-bearing_w8kq.md)**

## What's in it

Twenty-two chapters, from concurrency and clocks, distributed impossibility and queueing, through design patterns, TDD and abstraction, to the decisions a team never writes down.
Each chapter makes a claim and shows, with a worked case, where it stops.
The code is mostly Go, with Python second.

→ [All chapters](00_toc.md)

## How this book was written

The ideas, the arguments and the examples are mine. The prose was drafted by a large language model (Claude), one chapter at a time, then edited and sent back across 95 review passes, all in the commit history.
Every editorial decision, including the ones where the model's proposal was rejected, is in [`docs/DECISIONS.md`](docs/DECISIONS.md), so that claim can be checked rather than taken on trust.

**Status: v1.1.0.** All twenty-two chapters are written and have been read end to end. Corrections and disagreements welcome; open an issue.
How the book is put together, and how to cite it: [`docs/ABOUT.md`](docs/ABOUT.md).

By [Mike Akdeniz](https://github.com/mike-akdeniz)  ·  [CC BY-NC 4.0](LICENSE)
