package com.practicum.bionicproauth.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SessionData {
    private String userId;
    private String encryptedRefreshToken;
    private String accessToken;
    private long accessTokenExpiry;
}
