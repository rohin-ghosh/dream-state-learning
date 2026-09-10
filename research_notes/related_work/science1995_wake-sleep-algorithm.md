# The "wake-sleep" algorithm for unsupervised neural networks
Source: Science 268(5214):1158-1161, 1995. DOI: 10.1126/science.7761831 (not on arXiv)  
Authors: Geoffrey E. Hinton, Peter Dayan, Brendan J. Frey, Radford M. Neal

## Abstract
An unsupervised learning algorithm for a multilayer network of stochastic neurons is described. Bottom-up "recognition" connections convert the input into representations in successive hidden layers, and top-down "generative" connections reconstruct the representation in one layer from the representation in the layer above. In the "wake" phase, neurons are driven by recognition connections, and generative connections are adapted to increase the probability that they would reconstruct the correct activity vector in the layer below. In the "sleep" phase, neurons are driven by generative connections, and recognition connections are adapted to increase the probability that they would produce the correct activity vector in the layer above.

## Our differentiation
Claims: two alternating phases jointly minimize a variational bound (description length); companion paper is the Helmholtz machine (Dayan, Hinton, Neal, Zemel, Neural Computation 1995).
Mechanism: wake phase trains the generative model on real data encoded by the recognition net; sleep phase trains the recognition net on "fantasies" sampled from the generative model. Sleep learning uses only self-generated data — no external input.
Key point for us: sleep here does not consolidate content; it improves the *encoder/index* by training on dreams. The wake model and sleep model train each other.
Sleeper relevance: this is the original license for "thinker generates / sleeper compiles" — our sleeper rebuilding retrieval indexes and abstractions from generated/replayed traces is the structured-memory analog of sleep-phase recognition training; but wake-sleep has no dedup, GC, or multi-view organization, and consolidates only into weights.
