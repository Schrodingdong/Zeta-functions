package com.schrodi.zeta_runner.model;

import io.kubernetes.client.openapi.models.V2HorizontalPodAutoscaler;

import java.time.Instant;
import java.util.List;

public record ZetaDRHPA(
        Metadata metadata,
        Spec spec
) {

    public record Metadata(
            Instant creationTimestamp,
            String name,
            String namespace
    ) {}

    public record Spec(
            Integer minReplicas,
            Integer maxReplicas,
            ScaleTargetRef scaleTargetRef,
            List<Metric> metrics
    ) {}

    public record ScaleTargetRef(
            String apiVersion,
            String kind,
            String name
    ) {}

    public record Metric(
            String type,
            Resource resource
    ) {}

    public record Resource(
            String name,
            Target target
    ) {}

    public record Target(
            String type,
            Integer averageUtilization
    ) {}

    public static ZetaDRHPA from(V2HorizontalPodAutoscaler hpa) {
        return new ZetaDRHPA(
                new Metadata(
                        hpa.getMetadata().getCreationTimestamp().toInstant(),
                        hpa.getMetadata().getName(),
                        hpa.getMetadata().getNamespace()
                ),
                new Spec(
                        hpa.getSpec().getMinReplicas(),
                        hpa.getSpec().getMaxReplicas(),
                        new ScaleTargetRef(
                                hpa.getSpec().getScaleTargetRef().getApiVersion(),
                                hpa.getSpec().getScaleTargetRef().getKind(),
                                hpa.getSpec().getScaleTargetRef().getName()
                        ),
                        hpa.getSpec().getMetrics()
                                .stream()
                                .map(metric -> new Metric(
                                        metric.getType(),
                                        metric.getResource() == null
                                                ? null
                                                : new Resource(
                                                metric.getResource().getName(),
                                                new Target(
                                                        metric.getResource()
                                                                .getTarget()
                                                                .getType(),
                                                        metric.getResource()
                                                                .getTarget()
                                                                .getAverageUtilization()
                                                )
                                        )
                                ))
                                .toList()
                )
        );
    }
}