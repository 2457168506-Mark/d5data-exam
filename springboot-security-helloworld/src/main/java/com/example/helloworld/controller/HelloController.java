package com.example.helloworld.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 业务接口控制器。
 *
 * <p>题目要求的核心接口:GET /hello,返回字符串 "Hello World"。
 * 由于 SecurityConfig 中配置了 anyRequest().authenticated(),
 * 这个接口会被 Spring Security 自动保护——未登录访问会 302 到登录页,
 * 登录后携带 JSESSIONID 才会到达这个方法。
 */
@RestController
public class HelloController {

    /**
     * 返回 "Hello World"。
     *
     * <p>@RestController 会把方法返回的字符串直接作为 HTTP 响应体(text/plain)发回客户端,
     * 不会走 Thymeleaf/JSP 等模板引擎。
     */
    @GetMapping("/hello")
    public String hello() {
        return "Hello World";
    }
}
