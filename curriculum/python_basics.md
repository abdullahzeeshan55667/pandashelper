# Python Basics Curriculum

## Variables and Types
- **Why**: Names let you store data for reuse.
- **Example**:
  ```python
  name = "Ada"
  age = 20
  height_m = 1.7
  is_student = True
  ```
- **Checklist**: Can you choose descriptive names and identify `str`, `int`, `float`, and `bool`?

## Control Flow
- **Why**: Branching and looping make programs dynamic.
- **Example**:
  ```python
  for number in range(5):
      if number % 2 == 0:
          print(f"{number} is even")
      else:
          print(f"{number} is odd")
  ```
- **Checklist**: Can you write `if/elif/else` blocks and `for`/`while` loops?

## Functions
- **Why**: Functions package logic for reuse and testing.
- **Example**:
  ```python
  def add_tax(amount, rate=0.05):
      return amount * (1 + rate)

  total = add_tax(100)
  ```
- **Checklist**: Can you define functions with parameters, defaults, and return values?

## Collections
- **Why**: Lists, tuples, sets, and dictionaries organize data.
- **Example**:
  ```python
  languages = ["Python", "JavaScript", "Rust"]
  frameworks = {"web": "Django", "data": "pandas"}
  ```
- **Checklist**: Can you add/remove items and loop over collections?

## Modules and Packages
- **Why**: Modules let you structure larger codebases.
- **Example**:
  ```python
  import math

  print(math.sqrt(16))
  ```
- **Checklist**: Can you explain import paths and the role of `__init__.py`?
