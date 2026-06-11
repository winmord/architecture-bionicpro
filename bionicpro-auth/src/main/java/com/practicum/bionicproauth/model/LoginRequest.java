package com.practicum.bionicproauth.model;

import lombok.Data;

@Data
public class LoginRequest {
    private String code;
    private String codeVerifier;
}
