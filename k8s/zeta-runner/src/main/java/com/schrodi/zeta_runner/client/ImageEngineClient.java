package com.schrodi.zeta_runner.client;

import com.schrodi.zeta_runner.dto.ImageInfoResponse;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.service.annotation.HttpExchange;
import org.springframework.web.service.annotation.PostExchange;

@HttpExchange
public interface ImageEngineClient {
    @PostExchange(url = "/build")
    ImageInfoResponse buildImage(@RequestPart  MultiValueMap<String, Object> body);
}
