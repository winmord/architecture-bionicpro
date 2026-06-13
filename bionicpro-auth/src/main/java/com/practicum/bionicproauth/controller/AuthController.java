package com.practicum.bionicproauth.controller;

import com.practicum.bionicproauth.model.LoginRequest;
import com.practicum.bionicproauth.model.SessionData;
import com.practicum.bionicproauth.service.AuthService;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@CrossOrigin(origins = "http://localhost:3000", allowCredentials = "true")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/auth/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request, HttpServletResponse response) {
        try {
            String sessionId = authService.createSession(request.getCode(), request.getCodeVerifier());

            Cookie cookie = new Cookie("SESSION_ID", sessionId);
            cookie.setHttpOnly(true);
            cookie.setSecure(true);
            cookie.setPath("/");
            cookie.setMaxAge(7200);
            response.addCookie(cookie);

            return ResponseEntity.ok(Map.of("status", "ok"));
        } catch (Exception e) {
            return ResponseEntity.status(401).body(Map.of("error", "Authentication failed: " + e.getMessage()));
        }
    }

    @PostMapping("/auth/logout")
    public ResponseEntity<?> logout(HttpServletRequest request, HttpServletResponse response) {
        String sessionId = getSessionIdFromCookie(request);
        if (sessionId != null) {
            authService.deleteSession(sessionId);
        }

        Cookie cookie = new Cookie("SESSION_ID", "");
        cookie.setHttpOnly(true);
        cookie.setSecure(true);
        cookie.setPath("/");
        cookie.setMaxAge(0);
        response.addCookie(cookie);

        return ResponseEntity.ok(Map.of("status", "ok"));
    }

    @GetMapping("/auth/check")
    public ResponseEntity<?> checkSession(HttpServletRequest request) {
        String sessionId = getSessionIdFromCookie(request);
        if (sessionId == null) {
            return ResponseEntity.status(401).body(Map.of("authenticated", false));
        }

        SessionData session = authService.getSession(sessionId);
        if (session == null) {
            return ResponseEntity.status(401).body(Map.of("authenticated", false));
        }

        return ResponseEntity.ok(Map.of(
                "authenticated", true,
                "userId", session.getUserId()
        ));
    }

    @GetMapping("/auth/user")
    public ResponseEntity<?> getUser(HttpServletRequest request) {
        String sessionId = getSessionIdFromCookie(request);
        if (sessionId == null) {
            return ResponseEntity.status(401).body(Map.of("error", "No session"));
        }

        SessionData session = authService.getSession(sessionId);
        if (session == null) {
            return ResponseEntity.status(401).body(Map.of("error", "Invalid session"));
        }

        if (authService.isAccessTokenExpired(session)) {
            try {
                authService.refreshAccessToken(sessionId);
            } catch (Exception e) {
                return ResponseEntity.status(401).body(Map.of("error", "Token refresh failed"));
            }
        }

        return ResponseEntity.ok(Map.of("userId", session.getUserId()));
    }

    private String getSessionIdFromCookie(HttpServletRequest request) {
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if ("SESSION_ID".equals(cookie.getName())) {
                    return cookie.getValue();
                }
            }
        }
        return null;
    }
}
