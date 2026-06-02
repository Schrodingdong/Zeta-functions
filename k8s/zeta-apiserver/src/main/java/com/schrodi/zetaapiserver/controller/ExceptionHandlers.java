package com.schrodi.zetaapiserver.controller;

import com.schrodi.zetaapiserver.dto.ApiErrorResponse;
import com.schrodi.zetaapiserver.exception.ZetaNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;

@RestControllerAdvice
public class ExceptionHandlers {
    @ExceptionHandler(ZetaNotFoundException.class)
    public ResponseEntity<ApiErrorResponse> handleZetaNotFoundException(ZetaNotFoundException e){
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(
                new ApiErrorResponse(e.getMessage(), LocalDateTime.now())
        );
    }
}
