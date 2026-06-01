package com.schrodi.zeta_runner.model;

import tools.jackson.databind.JsonNode;

import java.util.Map;

public record ZetaRunner(
    String name,
    Map<String, JsonNode> objects
) { }
