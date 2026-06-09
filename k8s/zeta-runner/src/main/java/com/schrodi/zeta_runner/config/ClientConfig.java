package com.schrodi.zeta_runner.config;

import com.schrodi.zeta_runner.client.ImageEngineClient;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
@ConfigurationProperties("app.image-engine")
public class ClientConfig {
    private String url;

    @Bean
    RestClient restClient() {
        return RestClient.builder()
                .requestInterceptor((request, body, execution) -> {
                    System.out.println("Headers: " + request.getHeaders());
                    System.out.println("Body length: " + body.length);
                    return execution.execute(request, body);
                })
                .baseUrl(url)
                .build();
    }

    @Bean
    ImageEngineClient imageEngineClient(RestClient restClient) {
        RestClientAdapter adapter = RestClientAdapter.create(restClient);

        HttpServiceProxyFactory factory =
                HttpServiceProxyFactory.builderFor(adapter).build();

        return factory.createClient(ImageEngineClient.class);
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }
}
