FROM python:alpine3.17

# Run every 12 hours
ENV SLEEPTIME=43200

WORKDIR /guide

COPY GuideScraper.py GuideScraper.py
COPY entrypoint.sh entrypoint.sh

CMD ["sh", "entrypoint.sh"]
