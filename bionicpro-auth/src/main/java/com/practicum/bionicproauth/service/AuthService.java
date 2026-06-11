package com.practicum.bionicproauth.service;

import com.practicum.bionicproauth.model.SessionData;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final TokenService tokenService;
    private final EncryptionService encryptionService;

    private final Map<String, SessionData> sessions = new ConcurrentHashMap<>();

    @Value("${security.access-token-ttl}")
    private long accessTokenTtl;

    @Value("${security.session-ttl}")
    private long sessionTtl;

    public String createSession(String code, String codeVerifier) throws Exception {
        Map<String, Object> tokens = tokenService.exchangeCodeForTokens(code, codeVerifier);

        String accessToken = (String) tokens.get("access_token");
        String refreshToken = (String) tokens.get("refresh_token");
        String userId = extractUserId(accessToken);

        SessionData sessionData = new SessionData();
        sessionData.setUserId(userId);
        sessionData.setEncryptedRefreshToken(encryptionService.encrypt(refreshToken));
        sessionData.setAccessToken(accessToken);
        sessionData.setAccessTokenExpiry(System.currentTimeMillis() + (accessTokenTtl * 1000));

        String sessionId = UUID.randomUUID().toString();
        sessions.put(sessionId, sessionData);

        scheduleSessionRemoval(sessionId, sessionTtl);

        return sessionId;
    }

    public SessionData getSession(String sessionId) {
        return sessions.get(sessionId);
    }

    public boolean refreshAccessToken(String sessionId) throws Exception {
        SessionData session = sessions.get(sessionId);
        if (session == null) {
            return false;
        }

        String decryptedRefresh = encryptionService.decrypt(session.getEncryptedRefreshToken());
        Map<String, Object> newTokens = tokenService.refreshAccessToken(decryptedRefresh);

        String newAccessToken = (String) newTokens.get("access_token");
        session.setAccessToken(newAccessToken);
        session.setAccessTokenExpiry(System.currentTimeMillis() + (accessTokenTtl * 1000));

        if (newTokens.containsKey("refresh_token")) {
            String newRefreshToken = (String) newTokens.get("refresh_token");
            session.setEncryptedRefreshToken(encryptionService.encrypt(newRefreshToken));
        }

        sessions.put(sessionId, session);
        return true;
    }

    public String rotateSession(String oldSessionId) {
        SessionData session = sessions.remove(oldSessionId);
        if (session == null) return null;

        String newSessionId = UUID.randomUUID().toString();
        sessions.put(newSessionId, session);

        return newSessionId;
    }

    public void deleteSession(String sessionId) {
        sessions.remove(sessionId);
    }

    public boolean isAccessTokenExpired(SessionData session) {
        return System.currentTimeMillis() >= session.getAccessTokenExpiry();
    }

    private String extractUserId(String accessToken) {
        String[] parts = accessToken.split("\\.");
        if (parts.length == 3) {
            String payload = new String(java.util.Base64.getDecoder().decode(parts[1]));
            String search = "\"sub\":\"";
            int start = payload.indexOf(search);
            if (start != -1) {
                start += search.length();
                int end = payload.indexOf("\"", start);
                return payload.substring(start, end);
            }
        }
        return "unknown";
    }

    private void scheduleSessionRemoval(String sessionId, long ttlSeconds) {
        new Thread(() -> {
            try {
                Thread.sleep(ttlSeconds * 1000);
                sessions.remove(sessionId);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }).start();
    }
}