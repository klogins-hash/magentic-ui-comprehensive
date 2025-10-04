// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MagenticVoice",
    platforms: [
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "MagenticVoice",
            targets: ["MagenticVoice"]
        ),
    ],
    dependencies: [
        // Pipecat iOS SDK
        .package(url: "https://github.com/pipecat-ai/pipecat-client-ios-daily.git", from: "1.0.1"),
        // WebSocket client
        .package(url: "https://github.com/daltoniam/Starscream.git", from: "4.0.0"),
    ],
    targets: [
        .target(
            name: "MagenticVoice",
            dependencies: [
                .product(name: "PipecatClientIOSDaily", package: "pipecat-client-ios-daily"),
                .product(name: "Starscream", package: "Starscream"),
            ]
        ),
    ]
)
