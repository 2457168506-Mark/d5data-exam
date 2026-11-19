package com.example.helloworld;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/*
执行 main 方法会启动 SpringBoot 内嵌的 Tomcat 服务器(端口 8080),
并自动扫描当前包及其子包下的所有组件(Controller、Config 等)完成装配。
 */
@SpringBootApplication
public class HelloApplication {

    public static void main(String[] args) {
        SpringApplication.run(HelloApplication.class, args);
    }
}