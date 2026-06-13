package com.practicum.bionicproauth.filter;

import com.practicum.bionicproauth.model.SessionData;
import com.practicum.bionicproauth.service.AuthService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@RequiredArgsConstructor
public class SessionRotationFilter extends OncePerRequestFilter {

    private final AuthService authService;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws java.io.IOException, jakarta.servlet.ServletException {

        String path = request.getRequestURI();

        if (path.equals("/auth/login") || path.equals("/auth/logout") || path.equals("/auth/check")) {
            chain.doFilter(request, response);
            return;
        }

        Cookie[] cookies = request.getCookies();
        String sessionId = null;

        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if ("SESSION_ID".equals(cookie.getName())) {
                    sessionId = cookie.getValue();
                    break;
                }
            }
        }

        if (sessionId != null) {
            SessionData session = authService.getSession(sessionId);

            if (session != null) {
                if (authService.isAccessTokenExpired(session)) {
                    try {
                        boolean refreshed = authService.refreshAccessToken(sessionId);
                        if (!refreshed) {
                            response.setStatus(401);
                            return;
                        }
                    } catch (Exception e) {
                        response.setStatus(401);
                        return;
                    }
                }

                String newSessionId = authService.rotateSession(sessionId);
                if (newSessionId != null) {
                    Cookie newCookie = new Cookie("SESSION_ID", newSessionId);
                    newCookie.setHttpOnly(true);
                    newCookie.setSecure(true);
                    newCookie.setPath("/");
                    newCookie.setMaxAge(7200);
                    response.addCookie(newCookie);
                }
            }
        }

        chain.doFilter(request, response);
    }
}
