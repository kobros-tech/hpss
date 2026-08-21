# Statistical treatment of the allocation benchmark

The allocation benchmark separates deterministic dataset measurements from noisy runtime measurements.

## Collision metrics

For a fixed finite dataset, representation uniqueness, collision entries, collision pairs, and maximum collision-group size are computed exactly. They are not repeated random measurements, so a confidence interval over repeated executions would add no information: rerunning the same deterministic selector on the same dataset returns the same collision structure.

The correct interpretation is therefore descriptive for the supplied dataset. Generalization of collision behavior is addressed by repeating the experiment on independently structured datasets rather than by treating repeated executions as independent observations.

## Timing metrics

Selector timing is repeated independently for each allocation. The benchmark reports:

- median elapsed time;
- interquartile range (IQR);
- a percentile-bootstrap 95% confidence interval for the median;
- median throughput and its percentile-bootstrap 95% confidence interval.

The bootstrap uses a fixed seed for reproducibility. The default benchmark uses 15 timing repetitions and 2,000 bootstrap resamples; both can be changed from the command line.

These intervals quantify runtime variability. They should not be interpreted as confidence intervals for collision behavior or as evidence that two allocations are statistically different unless an appropriate paired comparison is performed.

## Research interpretation

The benchmark does not select a universal alpha from timing alone. Collision objectives are reported separately from speed, and the Pareto frontier is used to identify allocations that are not dominated simultaneously on uniqueness, collision pairs, and throughput.
