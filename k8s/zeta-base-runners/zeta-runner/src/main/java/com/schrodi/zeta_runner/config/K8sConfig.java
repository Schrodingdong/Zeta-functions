package com.schrodi.zeta_runner.config;

import io.kubernetes.client.openapi.ApiClient;
import io.kubernetes.client.util.Config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class K8sConfig {
    @Bean
    public ApiClient apiClient() {
        try {
            ApiClient k8sClient = Config.defaultClient();
            io.kubernetes.client.openapi.Configuration.setDefaultApiClient(k8sClient);
            return k8sClient;
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
