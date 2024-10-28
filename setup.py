from setuptools import setup, find_packages

# Safely read the README.md file with UTF-8 encoding
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rms_transcriber',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'google-cloud-speech',
        'pypubsub',
        'openai',
        'markdown2',
        'wxPython', 'wxasync',
    ],
    entry_points={
        'console_scripts': [
            'rms=rms_transcriber.rms:main',
        ],
    },
    include_package_data=True,
    author='Alex Buzunov',
    author_email='alex_buz@yahoo.com',
    description='An AI-powered Resumable Microphone Streaming Transcribe for Google Speech',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/myaichat/rms_transcriber',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    project_urls={
        'Source': 'https://github.com/myaichat/rms_transcriber',
        'Tracker': 'https://github.com/myaichat/rms_transcriber/issues',
    },
    changelog = """
    Version 1.0.0:
    - Added LeftPanel for transcription display
    """
)