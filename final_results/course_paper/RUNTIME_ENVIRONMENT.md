# Corrected-suite runtime environment

- Execution policy: sequential, one ordered agent pair at a time
- Processor: Intel Core i5-9600K CPU @ 3.70 GHz
- Operating system: Windows 10, build 19045, 64 bit
- Python: CPython 3.12.13, MSC v.1944, 64 bit
- Search revision: `public_information_adversarial_v2`
- Timing statistic: total monotonic action-selection time divided by non-pass decisions

Sequential execution was retained because concurrent search processes would contend for CPU time and weaken the within-machine runtime comparison. The measurements remain implementation- and machine-specific; they are not portable complexity benchmarks.
