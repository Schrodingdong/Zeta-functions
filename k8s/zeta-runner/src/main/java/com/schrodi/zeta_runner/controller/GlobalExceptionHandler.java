package com.schrodi.zeta_runner.controller;

import com.schrodi.zeta_runner.dto.ApiErrorResponse;
import com.schrodi.zeta_runner.exceptions.ZetaNotDeployedException;
import com.schrodi.zeta_runner.exceptions.ZetaResourceNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;

@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ZetaResourceNotFoundException.class)
    public ResponseEntity<?> handleZetaResourceNotFoundException(Exception e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(
                new ApiErrorResponse(e.getMessage(), LocalDateTime.now())
        );
    }

    @ExceptionHandler(ZetaNotDeployedException.class)
    public ResponseEntity<?> handleZetaNotDeployedException(Exception e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(
                new ApiErrorResponse(e.getMessage(), LocalDateTime.now())
        );
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<?> handleRuntimeException(Exception e) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(
                new ApiErrorResponse(e.getMessage(), LocalDateTime.now())
        );
    }
}
