# Honey Encryption for Structured English Messages

An educational cryptography project implementing and evaluating honey encryption for a restricted set of English messages. The project scope has been approved by the course TA.

## Motivation

Password-based authenticated encryption provides a way to recognize successful password guesses through its authentication check. Honey encryption aims to make incorrect guesses produce plausible alternative messages, making the original harder to distinguish from decoys.

We will begin with a single template:

> Meet me at [location] on [day] at [time].

A bounded message space lets us build a distribution-transforming encoder (DTE), integrate password-based encryption, and evaluate the outputs without attempting to model unrestricted English.

This is a research and learning prototype, not a production security tool. Valid-looking outputs alone do not establish security.

## Core Goals

- [ ] Define the supported locations, days, and times.
- [ ] Specify message probabilities and document the initial uniform-distribution assumption.
- [ ] Define plausibility and evaluation criteria before implementation.
- [ ] Implement a DTE with randomized encoding and deterministic decoding.
- [ ] Verify that decoding an encoded message always recovers that message.
- [ ] Verify that uniformly random seeds decode according to the intended message distribution.
- [ ] Integrate a researched honey-encryption construction using established cryptographic libraries where appropriate.
- [ ] Verify correct-password recovery and valid outputs for incorrect passwords.
- [ ] Measure wrong-password output frequencies against the expected distribution.
- [ ] Document results, limitations, references, and AI assistance.

## Plausibility Criteria

1. **Format validity:** Every decoded output belongs to the supported template and message space.
2. **Distribution agreement:** Outputs from random seeds and sampled incorrect passwords approximately follow the predefined message probabilities. We will select statistical measures, sample sizes, and acceptance criteria before running the final evaluation.

These criteria apply only to our modeled message space. They do not prove that decoys are realistic for actual human communication. A wrong password can also produce the original message by chance, especially in a small message space.

## Basic Roadmap

### 1. Research and Design

- [ ] Read and cite the original honey-encryption work and DTE construction.
- [ ] Specify the threat model, message distribution, seed space, and ciphertext format.
- [ ] Review the construction and math before implementation, including mapping bias and seed-space coverage.
- [ ] Define correctness and distribution tests.

### 2. DTE Prototype

- [ ] Build message parsing, formatting, and indexing.
- [ ] Implement message-to-seed encoding and total seed-to-message decoding.
- [ ] Test boundary cases and all supported messages where practical.
- [ ] Evaluate the distribution of random-seed outputs.

### 3. Encryption Integration

- [ ] Select the password derivation and seed-encryption approach from the researched construction.
- [ ] Implement encryption, decryption, and a small command-line interface.
- [ ] Keep public parameters independent of whether a password guess is correct.
- [ ] Test repeatability of decryption, fresh encryption randomness, and correct-password recovery.

### 4. Evaluation

- [ ] Generate reproducible datasets of wrong-password outputs.
- [ ] Report format validity, expected versus observed frequencies, and distribution error.
- [ ] Record sample sizes, parameter choices, runtime, and experimental limitations.
- [ ] Investigate unexpected results and retain evidence for the paper.

### 5. Final Paper

Use LaTeX and the ACM Conference Proceedings Primary Article Template.

- [ ] **Introduction:** Motivation, problem, approach, and project contribution.
- [ ] **Background:** Honey encryption, DTEs, password guessing, and cited resources.
- [ ] **System design/methodology:** Architecture, assumptions, and evaluation design.
- [ ] **Implementation and testing/results:** Implementation details, correctness tests, and measured results.
- [ ] **Discussion:** Lessons learned, limitations, unsuccessful attempts, and future work.
- [ ] Document how AI supported research, methodology review, development, and analysis.

## Stretch Goals

The TA recommended prioritizing the base DTE and encryption scheme. The following are optional:

- [ ] Model unequal message probabilities.
- [ ] Explore attacker side information and non-uniform priors.
- [ ] Add another sentence template.
- [ ] Compare password-guessing behavior with an authenticated-encryption baseline.

## Research and Limitations

The paper will examine why extending the prototype to unrestricted English is difficult: realistic probability modeling, grammar and meaning, variable message length, dependencies between words, and information already known to an attacker. We will also discuss the integrity and tampering limitations of the chosen construction.

If broader extensions do not succeed, the deliverable remains a restricted working example, a reproducible evaluation, and a detailed explanation of the obstacles and potential future approaches.

## Current Status

Repository initialized with project documentation only. No implementation or experimental results yet.

## Minimum implementation
The working Python CLI, commented source, tests, usage notes, and example files
are in [minimum implementation](<minimum implementation/PROTOTYPE.md>).
This educational prototype does not complete the research and evaluation tasks above.
