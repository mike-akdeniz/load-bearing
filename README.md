# Load-Bearing

*Which Software Principles Hold, and Where They Stop*

By [Mike Akdeniz](https://github.com/mike-akdeniz)  ·  [CC BY-NC 4.0](LICENSE)

> **AccountRepository needs an interface. Depend on abstractions.**

Says the code review on your latest commit.
Your gut says the interface would be pure drudgery here, but you can't make that case convincingly, so you comply and move on.

A builder opening up a kitchen doesn't guess whether a wall can come out. They look at what rests on it.
Software advice comes with no such inspection: there is the sentence, and there is the confidence of the person who said it.

**Many claims you meet about software are one of five kinds, and the kind determines how much authority it has**, not the confidence of the person saying it, not their track record, not how widely it is repeated.

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
