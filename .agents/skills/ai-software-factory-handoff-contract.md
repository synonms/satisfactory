# AI Software Factory Workflow Enhancement

## Overview

This skill documents key enhancements made to the AI Software Factory workflow, specifically the introduction of a formal handoff contract. This ensures consistent information flow across agents and prevents miscommunication that causes work to be stuck or require rework.

## When to Use

Use this skill when:
- Working with AI Software Factory workflows
- Performing reviews or implementing work items in the AI Software Factory
- Needing to ensure information consistency between agents 
- Encountering issues related to handoff information format or quality

## Prerequisites

- Access to the AI Software Factory repository and its documentation
- Understanding of the SDLC workflow and agent responsibilities
- Knowledge of YAML frontmatter formats used throughout the system

## How to Run

1. When implementing work items, ensure all artifacts follow the AI Software Factory Handoff Contract format
2. During reviews, verify that artifacts meet the requirements in the handoff contract
3. Maintain consistency with existing workflows while implementing the new contract standards
4. Communicate any non-compliance issues to relevant parties for correction

## Quick Reference

- All handoff artifacts must begin with proper YAML frontmatter
- Frontmatter fields include workItem, chunk, iteration, agent, technology, outcome, filesChanged, and nextOwner
- The contract ensures information flows properly between agents
- Consistency in format prevents miscommunication and reduces rework

## Procedure

1. **Understand the contract**: Review the AI Software Factory Handoff Contract for complete structure requirements
2. **Apply the contract**: When creating artifacts, ensure all required fields are populated appropriately  
3. **Validate consistency**: During reviews, verify that frontmatter contents align with task requirements and implementation
4. **Maintain quality**: Enforce adherence to the contract throughout the workflow

## Pitfalls

- **Ignoring the contract format**: Not following the established handoff contract can cause agents to not understand what information they need to proceed
- **Incomplete frontmatter**: Missing required fields in YAML frontmatter make it impossible for subsequent agents to proceed correctly
- **Inconsistent metadata**: Varying formats between similar artifacts create confusion and require additional review time
- **Overlooking verification requirements**: Failing to validate that frontmatter content matches actual work done causes rework

## Verification

Before completing any task, verify:
- [ ] Artifact follows the YAML frontmatter structure exactly as defined in handoff-contract.md
- [ ] All required fields are present and correctly populated 
- [ ] The 'nextOwner' field correctly identifies the next agent in the workflow
- [ ] 'outcome' accurately reflects the implemented work results
- [ ] 'filesChanged' lists all actual files modified by this iteration
- [ ] All information in frontmatter aligns with task requirements and actual implementation

## Enhancement Details

The AI Software Factory now uses a formal handoff contract in `.agents/resources/handoff-contract.md` that:

1. Defines the exact structure of all handoff artifacts
2. Specifies required YAML frontmatter fields with descriptions  
3. Documents artifact types and their specific requirements
4. Establishes information flow protocols between agents
5. Provides validation requirements for completed artifacts

This contract enforces consistent information transfer between agents, greatly reducing the risk of work being blocked due to unclear or missing information.