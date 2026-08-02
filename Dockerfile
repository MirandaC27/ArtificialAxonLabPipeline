FROM eclipse-temurin:11-jdk AS java

FROM python:3.10-slim

WORKDIR /app

ENV FIJI_PATH=/opt/fiji
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="/opt/java/openjdk/bin:$PATH"

COPY --from=java /opt/java/openjdk /opt/java/openjdk

COPY requirements.txt ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Pin Fiji and MCIB3D so analysis is reproducible and needs no host Fiji install.
RUN curl -fsSL "https://downloads.imagej.net/fiji/archive/20250514-1117/fiji-linux64.zip" -o /tmp/fiji.zip \
    && unzip -q /tmp/fiji.zip -d /opt \
    && mv /opt/Fiji.app /opt/fiji \
    && rm /tmp/fiji.zip \
    && mkdir -p /opt/fiji/plugins/mcib3d-suite \
    && curl -fsSL "https://sites.imagej.net/Tboudier/plugins/mcib3d-suite/mcib3d-core-4.1.7b.jar-20250509161435" -o /opt/fiji/plugins/mcib3d-suite/mcib3d-core-4.1.7b.jar \
    && curl -fsSL "https://sites.imagej.net/Tboudier/plugins/mcib3d-suite/mcib3d_plugins-4.1.7b.jar-20250509161435" -o /opt/fiji/plugins/mcib3d-suite/mcib3d_plugins-4.1.7b.jar \
    && curl -fsSL "https://sites.imagej.net/Tboudier/plugins/mcib3d-suite/mcib3d_dev-0.0.2.jar-20220318160610" -o /opt/fiji/plugins/mcib3d-suite/mcib3d_dev-0.0.2.jar \
    && curl -fsSL "https://sites.imagej.net/Tboudier/plugins/mcib3d-suite/quickhull3d-1.0.0.jar-20220106101206" -o /opt/fiji/plugins/mcib3d-suite/quickhull3d-1.0.0.jar \
    && curl -fsSL "https://sites.imagej.net/Tboudier/plugins/mcib3d-suite/mcib3d-jipipe-0.0.3.jar-20220525112119" -o /opt/fiji/plugins/mcib3d-suite/mcib3d-jipipe-0.0.3.jar

RUN pip install --no-cache-dir --only-binary=greenlet -r requirements.txt

RUN python -c "import imagej, scyjava; scyjava.config.set_java_constraints(fetch='auto'); ij=imagej.init('/opt/fiji', mode='headless'); print(ij.getVersion()); ij.dispose()"

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]