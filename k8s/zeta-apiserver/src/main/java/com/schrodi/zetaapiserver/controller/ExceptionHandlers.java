package com.schrodi.zetaapiserver.controller;

import com.schrodi.zetaapiserver.dto.ApiErrorResponse;
import com.schrodi.zetaapiserver.exception.ZetaAlreadyDeployedException;
import com.schrodi.zetaapiserver.exception.ZetaNotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;

@RestControllerAdvice
public class ExceptionHandlers {
    private static final Logger log = LoggerFactory.getLogger(ExceptionHandlers.class);

    @ExceptionHandler(ZetaAlreadyDeployedException.class)
    public ResponseEntity<ApiErrorResponse> handleZetaAlreadyDeployedException(ZetaAlreadyDeployedException e){
        log.error(e.getMessage(), e);
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(
                new ApiErrorResponse(e.getMessage(), LocalDateTime.now())
        );
    }

    @ExceptionHandler(ZetaNotFoundException.class)
    public ResponseEntity<ApiErrorResponse> handleZetaNotFoundException(ZetaNotFoundException e){
        log.error(e.getMessage(), e);
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(
                new ApiErrorResponse(e.getMessage(), LocalDateTime.now())
        );
    }
}
