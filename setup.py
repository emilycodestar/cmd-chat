import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    description = fh.read()

setuptools.setup(
    name="cmd-chat",
    version="2.0.0",
    author="VoxHash Technologies",
    author_email="contact@voxhash.dev",
    # Use find_packages to correctly discover package names
    packages=setuptools.find_packages(exclude=("test", "tests", "docs")),
    description="Modern secured CMD chat with end-to-end encryption",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/VoxHash/cmd-chat",
    license='MIT',
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'cmd_chat = cmd_chat:main'
        ]
    },
    install_requires=[
        "sanic>=23.12.0",
        "requests>=2.31.0",
        "rsa>=4.9",
        "cryptography>=41.0.0",
        "colorama>=0.4.6",
        "pydantic>=2.5.0",
        "websocket-client>=1.6.0",
        "rich>=13.7.0"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Security :: Cryptography",
    ],
    keywords="chat, encryption, secure, websocket, cli, console",
)